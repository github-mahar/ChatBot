import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

load_dotenv()

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
if cred_path:
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        # Initialization errors will be logged; the app will still start for dry development
        print("Failed to initialize Firebase Admin:", e)
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
