# ChatBot FYP

This repository contains a full-stack multi-turn AI chatbot.

Important: this repo must NOT contain secrets. Add your own secret files locally after cloning.

Local setup

1. Create local env files (do NOT commit them):

  - Create `frontend/.env` using `frontend/.env.example` as a template.
  - Create `backend/.env` using `backend/.env.example` as a template.

2. Add Firebase service account JSON:

  - Download the service account JSON from Firebase Console (Project Settings → Service accounts → Generate new private key).
  - Place the file at `backend/serviceAccountKey.json` (this path is ignored by `.gitignore`).

3. Install dependencies and run backend:

```bash
cd backend
python -m pip install -r requirements.txt
& "d:/My Web work/ChatBot/.venv/Scripts/python.exe" -m uvicorn backend.main:app --reload --port 8000
```

4. Install and run Ollama locally (required for model responses):

```powershell
# check installation
ollama --version
# pull the LLaMA 3 model
ollama pull llama3
# start Ollama (platform-specific - see ollama docs)
ollama serve
```

5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Security / GitHub

- `.gitignore` excludes `backend/serviceAccountKey.json`, `backend/.env`, and `frontend/.env`.
- If you accidentally committed secrets, remove them from history using `git rm --cached <file>` and follow GitHub instructions to purge sensitive data.

If you want, I can help run the commands to start Ollama now and verify `/chat/message` end-to-end.