# Story2Art

Story2Art is a full-stack AI story-to-image generator that turns written stories into polished visual prompts and AI-generated artwork. It combines a FastAPI backend with a Vite + React + Tailwind frontend and supports MongoDB Atlas as the primary data store while keeping SQLite as a local fallback.

## Features

- Story input and AI prompt enhancement
- Multiple visual styles and aspect ratios
- AI image generation through the OpenAI Images API
- MongoDB Atlas-ready SaaS storage with SQLite fallback for local development
- User auth, credits, gallery, pricing, and admin workflows
- Responsive premium dark theme UI

## Project structure

```text
story2art/
├── frontend/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── backend/
│   ├── app/
│   ├── generated_images/
│   ├── .env.example
│   ├── requirements.txt
│   └── story2art.db
├── .gitignore
├── README.md
└── .env.example
```

## Backend setup

```bash
cd story2art/backend
python -m venv .venv
# Windows:
# .venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
```

Set your keys in backend/.env:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-image-1
DATABASE_URL=sqlite:///./story2art.db
FRONTEND_URL=http://localhost:5173
JWT_SECRET=<at-least-32-random-characters>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=your-verified-sender@example.com
SMTP_FROM_NAME=Story2Art
WELCOME_CREDITS=25
DEFAULT_CREDIT_COST=5
```

Generate a strong JWT secret before using the app:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Password reset requires a working SMTP server and a strong `JWT_SECRET`. Reset codes expire after five minutes, are single-use, and can be requested once per minute (with additional per-email and per-IP limits). The API returns the same generic response for registered and unregistered email addresses. If SMTP delivery fails, the code is invalidated and the failure is recorded without logging the address or code. Configure SMTP before expecting reset emails; an API response alone does not confirm delivery.

Important: if MONGODB_URI is left empty, the app automatically falls back to the local SQLite database. When a valid Atlas URI is present, MongoDB becomes the primary database.

Run the backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend setup

```bash
cd story2art/frontend
npm install
npm run dev -- --host 0.0.0.0
```

## Access URLs

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Notes

- Without an OpenAI API key, the backend returns helpful errors instead of fake images.
- Generated images are stored in backend/generated_images.
- The app uses MongoDB Atlas when MONGODB_URI is configured; otherwise it falls back to SQLite for local development.
- SQLite startup migrations preserve existing data while adding authentication token-version and password-reset tables.
- Password reset endpoints: `POST /api/auth/forgot-password`, `POST /api/auth/verify-otp`, `POST /api/auth/resend-otp`, and `POST /api/auth/reset-password`.

## Testing

```bash
curl http://localhost:8000/
curl http://localhost:8000/docs
curl http://localhost:8000/api/health
python -m unittest discover -s tests -v
```
