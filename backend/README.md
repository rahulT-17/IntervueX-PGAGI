Backend Service
===============

Run commands from this folder.

Quickstart
----------
1) `pip install -r requirements.txt`
2) `copy .env.example .env`
3) `python -m app.db.run_init`
4) `uvicorn app.main:app --reload`

Notes
-----
- Put ingestion docs under `data/docs`.
- Chroma vectors persist under `data/chroma`.
