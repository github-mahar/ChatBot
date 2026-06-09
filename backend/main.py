import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

load_dotenv()
# Also load backend/.env explicitly if present (helps when running from project root)
try:
    load_dotenv(os.path.join(os.getcwd(), "backend", ".env"))
except Exception:
    pass

app = FastAPI()

origins = [os.getenv("FRONTEND_URL", "http://localhost:5173")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
# Fallback: if env var not set, try the local backend/serviceAccountKey.json
if not cred_path:
    fallback = os.path.join(os.getcwd(), "backend", "serviceAccountKey.json")
    if os.path.exists(fallback):
        cred_path = fallback

if cred_path:
    # Resolve candidate paths for the credential file to handle relative vs cwd differences
    candidates = [cred_path, os.path.join(os.getcwd(), cred_path), os.path.join(os.getcwd(), "backend", os.path.basename(cred_path))]
    found = None
    for p in candidates:
        try:
            if os.path.exists(p):
                found = p
                break
        except Exception:
            continue

    if found:
        try:
            cred = credentials.Certificate(found)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print("Failed to initialize Firebase Admin:", e)
    else:
        print(f"FIREBASE_SERVICE_ACCOUNT_PATH set to '{cred_path}', but file not found in candidates: {candidates}")
else:
    print("FIREBASE_SERVICE_ACCOUNT_PATH not set; skipping Firebase Admin init")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# Include placeholder routers
try:
    from backend.routes.chat import router as chat_router
    from backend.routes.sessions import router as sessions_router
    from backend.routes.analytics import router as analytics_router

    app.include_router(chat_router)
    app.include_router(sessions_router)
    app.include_router(analytics_router)
except Exception as e:
    print("Could not include routers:", e)
