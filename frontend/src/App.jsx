import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const uiSteps = [
  { id: 1, label: "Start Session" },
  { id: 2, label: "Upload + Setup" },
  { id: 3, label: "Question + Answer" },
  { id: 4, label: "Summary" },
];

function normalizeSkills(skillsText) {
  return skillsText
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

function calcSummaryScore(summary) {
  if (!summary || !summary.questions?.length) return 0;
  const answerFeedback = summary.questions.flatMap((q) => q.answers || []);
  if (!answerFeedback.length) return 0;

  const scores = answerFeedback.map((a) => {
    const strengths = a.generated_feedback?.strengths?.length || 0;
    const missing = a.generated_feedback?.missing_concepts?.length || 0;
    const total = strengths + missing;
    if (!total) return 50;
    return Math.round((strengths / total) * 100);
  });
  const total = scores.reduce((sum, value) => sum + value, 0);
  return Math.round(total / scores.length);
}

function getTopicBreakdown(summary) {
  if (!summary?.questions?.length) return [];
  const map = new Map();
  summary.questions.forEach((q) => {
    const key = q.topic || "General";
    map.set(key, (map.get(key) || 0) + 1);
  });
  const max = Math.max(...map.values());
  return [...map.entries()].map(([topic, count]) => ({
    topic,
    count,
    percent: Math.round((count / max) * 100),
  }));
}

async function apiCall(path, init = {}) {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (body?.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }
  return response.json();
}

export default function App() {
  const [activeStep, setActiveStep] = useState(1);
  const [userName, setUserName] = useState("Rahul");
  const [role, setRole] = useState("backend");
  const [experience, setExperience] = useState("Intermediate");
  const [resumeFile, setResumeFile] = useState(null);
  const [manualSkills, setManualSkills] = useState("");
  const [context, setContext] = useState("Interview for a mid-level backend engineer.");
  const [sessionId, setSessionId] = useState(null);
  const [resumeId, setResumeId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [currentQuestionId, setCurrentQuestionId] = useState(null);
  const [answerText, setAnswerText] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [summary, setSummary] = useState(null);
  const [retrievalQuery, setRetrievalQuery] = useState("");
  const [retrievalSources, setRetrievalSources] = useState([]);
  const [status, setStatus] = useState("Ready");
  const [busy, setBusy] = useState(false);

  const summaryScore = useMemo(() => calcSummaryScore(summary), [summary]);
  const topicBreakdown = useMemo(() => getTopicBreakdown(summary), [summary]);
  const totalQuestions = summary?.questions?.length || 0;
  const answeredQuestions = summary?.questions?.filter((q) => (q.answers || []).length > 0).length || 0;

  useEffect(() => {
    if (activeStep === 4 && sessionId && !summary) {
      fetchSummary();
    }
  }, [activeStep]); // eslint-disable-line react-hooks/exhaustive-deps

  async function startSession() {
    try {
      setBusy(true);
      setStatus("Creating interview session...");
      const sessionResp = await apiCall("/interview/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_name: userName, role }),
      });
      setSessionId(sessionResp.session_id);
      setCurrentQuestion("");
      setCurrentQuestionId(null);
      setFeedback(null);
      setSummary(null);
      setStatus(`Session started (ID: ${sessionResp.session_id}).`);
      setActiveStep(2);
    } catch (error) {
      setStatus(`Start failed: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function setupInterviewAndContinue() {
    if (!sessionId) {
      setStatus("Start session first.");
      return;
    }
    try {
      setBusy(true);
      if (resumeFile) {
        setStatus("Uploading and parsing resume...");
        const form = new FormData();
        form.append("file", resumeFile);
        form.append("session_id", String(sessionId));
        form.append("target_role", role);

        const resumeResp = await apiCall("/resume/upload", {
          method: "POST",
          body: form,
        });
        setResumeId(resumeResp.resume_id);

        if (!manualSkills && resumeResp.parsed_profile?.skills?.length) {
          setManualSkills(resumeResp.parsed_profile.skills.join(", "));
        }
      }

      setStatus("Ingesting docs into RAG store...");
      await apiCall("/rag/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role, docs_path: "data/docs" }),
      });

      setStatus("Setup complete.");
      setActiveStep(3);
    } catch (error) {
      setStatus(`Setup failed: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function generateQuestion() {
    if (!sessionId) {
      setStatus("Start session first.");
      return;
    }
    try {
      setBusy(true);
      setStatus("Retrieving context and generating question...");
      const skills = normalizeSkills(manualSkills);

      const retrievePayload = {
        session_id: sessionId,
        role,
        skills,
        context,
        query: null,
        top_k: 6,
      };
      if (resumeId) retrievePayload.resume_id = resumeId;

      const retrieveResp = await apiCall("/rag/retrieve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(retrievePayload),
      });
      setRetrievalQuery(retrieveResp.query || "");
      setRetrievalSources(retrieveResp.chunks || []);

      const questionPayload = {
        session_id: sessionId,
        role,
        skills,
        context,
        query: null,
        top_k: 6,
      };
      if (resumeId) questionPayload.resume_id = resumeId;

      const questionResp = await apiCall("/interview/question", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(questionPayload),
      });
      setCurrentQuestion(questionResp.question);
      setCurrentQuestionId(questionResp.question_id);
      setAnswerText("");
      setFeedback(null);
      setStatus("Question ready.");
    } catch (error) {
      setStatus(`Question generation failed: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function submitAnswerAndContinue() {
    if (!currentQuestionId) {
      setStatus("Generate a question first.");
      return;
    }
    if (!answerText.trim()) {
      setStatus("Write your answer first.");
      return;
    }
    try {
      setBusy(true);
      setStatus("Evaluating answer...");
      const answerResp = await apiCall("/interview/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: currentQuestionId,
          answer: answerText,
        }),
      });
      setFeedback(answerResp.generated_feedback || null);
      setStatus("Answer submitted successfully.");
      setActiveStep(4);
    } catch (error) {
      setStatus(`Answer submission failed: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function fetchSummary() {
    if (!sessionId) {
      setStatus("Start session first.");
      return;
    }
    try {
      setBusy(true);
      setStatus("Loading summary...");
      const summaryResp = await apiCall(`/interview/${sessionId}/summary?include_chunks=false`);
      setSummary(summaryResp);
      setStatus("Summary loaded.");
    } catch (error) {
      setStatus(`Summary failed: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <aside className="left-rail card">
        <h1 className="brand">
          <span>Intervue</span>X
        </h1>
        <p className="subtitle">Contextual. Intelligent. Traceable.</p>

        <section className="flow card-inner">
          <h3>Interview Flow</h3>
          <div className="steps">
            {uiSteps.map((step) => (
              <div className={`step ${activeStep >= step.id ? "active" : ""}`} key={step.id}>
                <span>{step.id}</span>
                <small>{step.label}</small>
              </div>
            ))}
          </div>
        </section>

        <section className="highlights card-inner">
          <p><strong>Contextual Questions</strong> tailored to role and skills.</p>
          <p><strong>AI Feedback</strong> with strengths and missing concepts.</p>
          <p><strong>Traceability</strong> via retrieval query and sources.</p>
          <p><strong>Smart Summary</strong> of full interview performance.</p>
        </section>
      </aside>

      <main className="dashboard single">
        <section className="panel card panel-single">
          <header className="panel-header wizard-head">
            <span className="badge">{activeStep}</span>
            <h2>{uiSteps.find((s) => s.id === activeStep)?.label}</h2>
          </header>

          <div className="wizard-nav">
            {uiSteps.map((step) => (
              <button
                key={step.id}
                className={`nav-btn ${activeStep === step.id ? "current" : ""}`}
                onClick={() => setActiveStep(step.id)}
                disabled={busy || (step.id > 1 && !sessionId)}
              >
                {step.id}. {step.label}
              </button>
            ))}
          </div>

          {activeStep === 1 ? (
            <>
              <div className="panel-body split">
                <div className="form">
                  <label>Name</label>
                  <input value={userName} onChange={(e) => setUserName(e.target.value)} />

                  <label>Role</label>
                  <select value={role} onChange={(e) => setRole(e.target.value)}>
                    <option value="backend">Backend Engineer</option>
                    <option value="data">Data Engineer</option>
                    <option value="ml">ML Engineer</option>
                  </select>

                  <label>Experience Level</label>
                  <select value={experience} onChange={(e) => setExperience(e.target.value)}>
                    <option>Beginner</option>
                    <option>Intermediate</option>
                    <option>Advanced</option>
                  </select>
                </div>
              </div>
              <div className="actions">
                <button className="btn primary" onClick={startSession} disabled={busy}>
                  Start Session & Continue
                </button>
                <div className="meta">{sessionId ? `Session: ${sessionId}` : "No session yet"}</div>
              </div>
            </>
          ) : null}

          {activeStep === 2 ? (
            <>
              <div className="panel-body split">
                <div className="form">
                  <label>Upload Resume</label>
                  <input type="file" accept=".pdf,.docx,.txt,.md" onChange={(e) => setResumeFile(e.target.files?.[0] || null)} />

                  <label>Skills (comma separated)</label>
                  <input
                    value={manualSkills}
                    onChange={(e) => setManualSkills(e.target.value)}
                    placeholder="FastAPI, SQLAlchemy, PostgreSQL"
                  />

                  <label>Interview Context</label>
                  <textarea value={context} onChange={(e) => setContext(e.target.value)} rows={3} />
                </div>
              </div>
              <div className="actions">
                <button className="btn ghost" onClick={() => setActiveStep(1)} disabled={busy}>
                  Back
                </button>
                <button className="btn primary" onClick={setupInterviewAndContinue} disabled={busy || !sessionId}>
                  Save Setup & Continue
                </button>
                <div className="meta">{resumeId ? `Resume: ${resumeId}` : "Resume optional"}</div>
              </div>
            </>
          ) : null}

          {activeStep === 3 ? (
            <>
              <div className="question">{currentQuestion || "Generate your contextual interview question."}</div>
              {retrievalQuery ? <p className="query">Retrieval Query: {retrievalQuery}</p> : null}

              <div className="actions">
                <button className="btn ghost" onClick={() => setActiveStep(2)} disabled={busy}>
                  Back
                </button>
                <button className="btn primary" onClick={generateQuestion} disabled={busy || !sessionId}>
                  Generate Question
                </button>
              </div>

              <label>Your Answer</label>
              <textarea
                rows={6}
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                placeholder="Type your answer..."
              />
              <div className="actions">
                <button className="btn primary" onClick={submitAnswerAndContinue} disabled={busy || !currentQuestionId}>
                  Submit Answer & Continue
                </button>
              </div>
            </>
          ) : null}

          {activeStep === 4 ? (
            <>
              <div className="summary-head">
                <div className="score-ring">
                  <div className="ring">{summaryScore}%</div>
                  <small>Overall</small>
                </div>
                <div className="summary-stats">
                  <p><strong>{totalQuestions}</strong> Questions Asked</p>
                  <p><strong>{answeredQuestions}</strong> Answered</p>
                  <p><strong>{retrievalSources.length}</strong> Current Sources</p>
                </div>
              </div>

              <div className="feedback-grid">
                <div className="feedback-card">
                  <h4>Strengths</h4>
                  <ul>
                    {(feedback?.strengths || []).map((item, idx) => (
                      <li key={`${item}-${idx}`}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div className="feedback-card">
                  <h4>Missing Concepts</h4>
                  <ul>
                    {(feedback?.missing_concepts || []).map((item, idx) => (
                      <li key={`${item}-${idx}`}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div className="feedback-card wide">
                  <h4>Overall Feedback</h4>
                  <p>{feedback?.overall_feedback || "Submit an answer to view AI feedback."}</p>
                </div>
              </div>

              <div className="topic-breakdown">
                <h4>Topic Breakdown</h4>
                {topicBreakdown.map((row) => (
                  <div className="bar-row" key={row.topic}>
                    <span>{row.topic}</span>
                    <div className="bar"><div style={{ width: `${row.percent}%` }} /></div>
                    <em>{row.count}</em>
                  </div>
                ))}
              </div>

              <div className="traceability">
                <h4>Traceability Sources</h4>
                <ol>
                  {retrievalSources.slice(0, 3).map((chunk, idx) => (
                    <li key={`${chunk.metadata?.source || "source"}-${idx}`}>
                      {chunk.metadata?.source || "Unknown source"}{" "}
                      <small>(score: {chunk.score ?? "n/a"})</small>
                    </li>
                  ))}
                </ol>
              </div>

              <div className="actions">
                <button className="btn ghost" onClick={() => setActiveStep(3)} disabled={busy}>
                  Back
                </button>
                <button className="btn primary" onClick={fetchSummary} disabled={busy || !sessionId}>
                  Refresh Summary
                </button>
              </div>
            </>
          ) : null}
        </section>
      </main>

      <aside className="right-rail card">
        <h3>Session Status</h3>
        <ul>
          <li><strong>Session:</strong> {sessionId || "Not started"}</li>
          <li><strong>Resume:</strong> {resumeId || "Not uploaded"}</li>
          <li><strong>Role:</strong> {role}</li>
          <li><strong>Experience:</strong> {experience}</li>
        </ul>
        <div className="status">{busy ? "Working..." : status}</div>
      </aside>
    </div>
  );
}
