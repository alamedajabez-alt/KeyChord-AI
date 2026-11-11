# KeyChord AI
Chord and note transcription for keyboard players. See `docs/ARCHITECTURE.md`.

## Status
Phase 1 (setup & architecture) complete. No analysis features exist yet; nothing in this repo fakes results.

## Setup
```bash
cp .env.example backend/.env
docker compose -f infra/docker-compose.yml up -d        # PostgreSQL

cd backend
python3.11 -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload                            # http://localhost:8000/docs
pytest

# new terminal
cd frontend && npm install && npm run dev                # http://localhost:5173
```
Install `ffmpeg` on your system for M4A support (Phase 3+). `requirements-audio.txt` is installed in Phase 4.
# KeyChord-AI
