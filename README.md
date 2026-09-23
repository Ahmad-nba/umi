# Feedback Watch Tower for UMI

Backend-first FastAPI prototype for managing the lifecycle of feedback and issue resolution.

## Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```
3. Start the app:
   ```bash
   uvicorn app.main:app --reload
   ```

## Run tests

```bash
pytest
```

## Demo

```bash
python -m scripts.demo
```

## Interactive CLI workspace

Operate the existing API workflow from the terminal:

```bash
python cli_test.py
```

Run an isolated, non-interactive lifecycle demo:

```bash
python cli_test.py --demo --fresh
```

Add `--verbose` to show the API calls issued by the CLI.

## Web application

The frontend has its own `package.json` under `web/`. Run npm commands from that directory:

```bash
cd web
npm install
npm run dev
```

Then open `http://127.0.0.1:3000`. Keep the FastAPI backend running separately on `http://127.0.0.1:8000`.
