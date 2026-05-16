# Complyr

Write an invoice validation rule in plain English. Complyr compiles it into deterministic XSLT and runs it against any UBL XML invoice. No XSLT knowledge needed, no engineering ticket required.

Built for the Complyance Hackathon 2026 by team Indent.

## What it does

You type something like:

> "Invoice must have a DueDate. Severity HIGH."

Complyr parses that into a typed Intermediate Representation, compiles it to XSLT 3.0, and runs it against your invoice. You get back a structured pass or fail with the exact XPath location of the problem.

The LLM (running locally via Ollama) only produces the IR. It never writes XSLT and never runs at validation time. Same rule in, same XSLT out, every time.

## Project structure

```
complyr/
  backend/       FastAPI app, compiler, Ollama parser, validation runtime
  frontend/      Next.js UI with rule editor and invoice viewer
  dataset/       Dataset generator scripts
  data/          Reference PINT AE invoice samples
```

## Getting started

**Backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Requires Ollama running locally with `llama3.2` pulled:

```bash
ollama pull llama3.2
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`. Backend runs on `http://localhost:8000`.

## API


| Method | Route                 | What it does                                   |
| ------ | --------------------- | ---------------------------------------------- |
| POST   | `/api/rules/parse`    | Parses English rule to IR + compiles XSLT      |
| POST   | `/api/rules/validate` | Runs an IR against an invoice XML              |
| POST   | `/api/rules/run`      | Full pipeline: text + XML file in, results out |
| GET    | `/health`             | Health check                                   |


---

## Tech stack

- **Ollama** (Llama 3.2, local) for NL to IR parsing
- **Python + lxml + Saxon-HE** for XSLT 3.0 compilation and execution
- **FastAPI** for the API layer
- **Next.js + TypeScript + Tailwind** for the frontend
- **Pydantic** for IR schema validation

