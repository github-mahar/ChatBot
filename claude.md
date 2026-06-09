# CLAUDE.md — Multi-Turn AI Chatbot FYP

## Project Overview

Build a full-stack multi-turn AI chatbot web application. The AI model is LLaMA 3 running locally via Ollama. The frontend is React + Tailwind CSS + Vite. The backend is FastAPI (Python). Auth and database use Firebase (Google OAuth + Firestore).

---

## Folder Structure

```
chatbot-fyp/
├── CLAUDE.md
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── firebase.js
│       ├── pages/
│       │   ├── LoginPage.jsx
│       │   ├── ChatPage.jsx
│       │   └── DashboardPage.jsx
│       └── components/
│           ├── ChatWindow.jsx
│           ├── MessageBubble.jsx
│           ├── FeedbackButtons.jsx
│           ├── SessionList.jsx
│           ├── Navbar.jsx
│           └── AnalyticsChart.jsx
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── routes/
│       ├── chat.py
│       ├── sessions.py
│       └── analytics.py
└── README.md
```

---

## Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Frontend    | React 18, Vite, Tailwind CSS v3   |
| Backend     | FastAPI, Python 3.11+             |
| AI Model    | LLaMA 3 via Ollama (local)        |
| Database    | Firebase Firestore                |
| Auth        | Firebase Auth (Google OAuth)      |
| Charts      | Recharts                          |
| HTTP Client | Axios                             |

---

## Environment Variables

### Frontend (`frontend/.env`)
```
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_BACKEND_URL=http://localhost:8000
```

### Backend (`backend/.env`)
```
FIREBASE_SERVICE_ACCOUNT_PATH=./serviceAccountKey.json
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
FRONTEND_URL=http://localhost:5173
```

---

## Backend Implementation

### `backend/requirements.txt`
```
fastapi
uvicorn[standard]
python-dotenv
httpx
firebase-admin
pydantic
```

### `backend/main.py`
- Create FastAPI app
- Add CORS middleware allowing `FRONTEND_URL` from `.env`
- Include routers: `/chat`, `/sessions`, `/analytics`
- On startup, initialize Firebase Admin SDK using service account JSON path from env

### `backend/routes/chat.py`

**POST `/chat/message`**

Request body:
```json
{
  "session_id": "string",
  "user_id": "string",
  "message": "string",
  "history": [
    { "role": "user", "content": "string" },
    { "role": "assistant", "content": "string" }
  ]
}
```

Logic:
1. Build the full message array from `history` + new user message
2. Send to Ollama at `POST http://localhost:11434/api/chat` with model `llama3` and `stream: false`
3. Extract `message.content` from Ollama response
4. Save the user message and AI response to Firestore under `sessions/{session_id}/messages` collection — each document has: `role`, `content`, `timestamp`
5. Update `sessions/{session_id}` document: set `last_updated` to now, increment `message_count`
6. Return `{ "response": "...", "session_id": "..." }`

**POST `/chat/feedback`**

Request body:
```json
{
  "session_id": "string",
  "message_id": "string",
  "feedback": "positive" | "negative"
}
```

Logic:
- Update the Firestore document `sessions/{session_id}/messages/{message_id}` with `feedback` field

### `backend/routes/sessions.py`

**GET `/sessions/{user_id}`**
- Query Firestore `sessions` collection where `user_id == user_id`
- Order by `last_updated` descending
- Return list of sessions: `[{ id, title, last_updated, message_count }]`

**POST `/sessions/new`**

Request body: `{ "user_id": "string", "title": "string" }`
- Create new document in Firestore `sessions` collection
- Fields: `user_id`, `title`, `created_at`, `last_updated`, `message_count: 0`
- Return `{ "session_id": "..." }`

**GET `/sessions/{session_id}/messages`**
- Get all documents from `sessions/{session_id}/messages` subcollection
- Order by `timestamp` ascending
- Return array of messages

**DELETE `/sessions/{session_id}`**
- Delete session document and all its messages subcollection documents

### `backend/routes/analytics.py`

**GET `/analytics/{user_id}`**
- Fetch all sessions for the user
- For each session, fetch its messages
- Compute and return:
  - `total_sessions`: count of sessions
  - `total_messages`: total user messages across all sessions
  - `positive_feedback`: count of messages with `feedback == "positive"`
  - `negative_feedback`: count of messages with `feedback == "negative"`
  - `messages_per_day`: array of `{ date: "YYYY-MM-DD", count: number }` for the last 14 days
  - `avg_messages_per_session`: float

---

## Frontend Implementation

### `frontend/src/firebase.js`
- Initialize Firebase app using `VITE_FIREBASE_*` env vars
- Export `auth` (Firebase Auth instance) and `db` (Firestore instance)
- Export `googleProvider` (GoogleAuthProvider instance)

### `frontend/src/App.jsx`
- Use `onAuthStateChanged` to track login state
- Routes:
  - `/` → if logged in redirect to `/chat`, else show `LoginPage`
  - `/chat` → protected, show `ChatPage`
  - `/dashboard` → protected, show `DashboardPage`
- Use React Router v6

### `frontend/src/pages/LoginPage.jsx`
- Centered card layout with app name "ChatBot AI" and tagline
- Single "Sign in with Google" button
- On click: call `signInWithPopup(auth, googleProvider)`
- On success: navigate to `/chat`
- Dark theme: background `#0f0f0f`, card `#1a1a1a`, accent color `#6366f1` (indigo)

### `frontend/src/pages/ChatPage.jsx`

Layout: two-column
- **Left sidebar (280px)**: SessionList component + "New Chat" button + user avatar + logout button
- **Right main area**: ChatWindow component

State:
- `sessions` — list of user's sessions
- `activeSessionId` — currently selected session
- `messages` — messages for active session

On mount:
- Fetch sessions from `GET /sessions/{user_id}`
- If no sessions exist, auto-create one titled "New Chat"

On new message:
- Append user message to `messages` state immediately (optimistic UI)
- Show typing indicator
- POST to `/chat/message` with full history
- Replace typing indicator with AI response

### `frontend/src/pages/DashboardPage.jsx`
- Fetch from `GET /analytics/{user_id}` on mount
- Display stat cards: Total Sessions, Total Messages, Positive Feedback %, Avg Messages/Session
- Line chart (Recharts): Messages per day over last 14 days
- Bar chart (Recharts): Positive vs Negative feedback count
- Back button to `/chat`

### `frontend/src/components/ChatWindow.jsx`
- Scrollable message list using `MessageBubble`
- Auto-scroll to bottom on new message (use `useRef` + `scrollIntoView`)
- Input bar at bottom: textarea (Enter to send, Shift+Enter for newline) + Send button
- Show typing indicator (three animated dots) while waiting for AI response

### `frontend/src/components/MessageBubble.jsx`
Props: `{ role, content, messageId, sessionId, feedback }`
- User messages: aligned right, indigo background
- AI messages: aligned left, dark gray background
- Below each AI message: `FeedbackButtons` component (only if `feedback` is not yet set)

### `frontend/src/components/FeedbackButtons.jsx`
Props: `{ messageId, sessionId, onFeedback }`
- Two icon buttons: 👍 and 👎
- On click: POST to `/chat/feedback`, then call `onFeedback(type)` to update local state
- After feedback is given: show the selected icon highlighted, hide the other

### `frontend/src/components/SessionList.jsx`
Props: `{ sessions, activeSessionId, onSelect, onDelete }`
- List of past sessions sorted by `last_updated`
- Each item: session title + last updated date
- Hover: show delete (trash) icon
- Click: switch active session and load its messages
- Active session: highlighted with indigo left border

### `frontend/src/components/Navbar.jsx`
- App name on the left
- "Dashboard" link and user profile photo + name on the right
- Logout button

### `frontend/src/components/AnalyticsChart.jsx`
Props: `{ data, type }` where type is `"line"` or `"bar"`
- Wrap Recharts `LineChart` or `BarChart` with responsive container
- Use indigo/purple color scheme consistent with app theme

---

## Design System

- **Background**: `#0f0f0f`
- **Surface**: `#1a1a1a`
- **Surface elevated**: `#242424`
- **Accent**: `#6366f1` (indigo-500)
- **Accent hover**: `#4f46e5` (indigo-600)
- **Text primary**: `#f4f4f5`
- **Text secondary**: `#a1a1aa`
- **Border**: `#2e2e2e`
- **Font**: Inter (load from Google Fonts)
- **Border radius**: `0.75rem` for cards, `0.5rem` for buttons, `1.5rem` for message bubbles

---

## Key Rules

1. **Never hardcode Firebase credentials** — always read from `VITE_FIREBASE_*` env vars
2. **Never hardcode backend URL** — always use `VITE_BACKEND_URL` env var
3. **All Firestore writes go through the backend** — frontend never writes to Firestore directly
4. **Frontend only handles UI state** — no business logic in components
5. **Every API call must have a try/catch** — show user-friendly error toasts on failure
6. **Protected routes**: redirect to `/` if user is not authenticated
7. **Ollama must be running locally** on port 11434 with `llama3` model pulled — the backend will fail gracefully with a 503 if Ollama is unreachable

---

## Build & Run Instructions (include in README.md)

### Prerequisites
- Node.js 18+
- Python 3.11+
- Ollama installed and running with LLaMA 3: `ollama pull llama3`
- Firebase project created with Firestore and Google Auth enabled
- Firebase service account JSON downloaded

### Backend
```bash
cd backend
pip install -r requirements.txt
# Add .env file with your values
# Place serviceAccountKey.json in backend/
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
# Add .env file with your Firebase config
npm run dev
```

---

## What to Build — Ordered Task List

1. Backend scaffold: FastAPI app + CORS + Firebase Admin init
2. Backend: `/chat/message` endpoint with Ollama integration
3. Backend: `/chat/feedback` endpoint
4. Backend: sessions CRUD endpoints
5. Backend: analytics endpoint
6. Frontend: Vite + React + Tailwind setup
7. Frontend: Firebase config + auth
8. Frontend: Login page with Google sign-in
9. Frontend: Protected route wrapper
10. Frontend: Chat page layout (sidebar + chat window)
11. Frontend: Session list + new session creation
12. Frontend: Chat window with message bubbles + typing indicator
13. Frontend: Feedback buttons
14. Frontend: Analytics/Dashboard page with Recharts
15. README with setup instructions