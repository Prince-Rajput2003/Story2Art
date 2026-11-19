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
APP_ENV=development
JWT_SECRET=<at-least-32-random-characters>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_gmail_address@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM_EMAIL=your_gmail_address@gmail.com
SMTP_FROM_NAME=Story2Art
WELCOME_CREDITS=25
DEFAULT_CREDIT_COST=5
```

Generate a strong JWT secret before using the app:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

For Gmail, set `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USERNAME` and `SMTP_FROM_EMAIL` to your Gmail address, and `SMTP_PASSWORD` to a Google App Password (not your account password). Never commit the populated `backend/.env` file. Password reset also requires a strong `JWT_SECRET`. OTPs expire after five minutes, are stored only as keyed hashes, allow five verification attempts, and can be resent once per 60 seconds. Development allows 10 requests per email and 30 per IP per hour; production allows 5 per email and 15 per IP per hour. Set `APP_ENV=production` in production. SMTP is checked before rate-limit counters are changed, and the API returns an error if SMTP delivery fails.

To clear only password-reset request counters in a local development SQLite database after testing, make sure `APP_ENV=development` is explicitly set in `backend/.env`, then run from `backend`:

```bash
python reset_password_reset_limits.py
```

The script refuses to run unless `APP_ENV=development`; it does not delete users, OTP challenges, or other application data.

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

## Render backend deployment

The repository includes a Render Blueprint at `render.yaml`. Create a Blueprint from the repository root, then provide:

- `DATABASE_URL`: a Render PostgreSQL connection string (the backend converts Render's `postgresql://` URL to the installed psycopg driver).
- `FRONTEND_URL`: the deployed frontend origin.
- `OPENAI_API_KEY` and Cloudflare credentials for image generation.
- Gmail SMTP username, App Password, and sender address for password-reset email.

The service uses Python 3.11.11 (also pinned in `.python-version`) to match the backend's tested dependency environment. Its build command installs `backend/requirements.txt`; its start command binds Uvicorn to Render's `$PORT`.

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
