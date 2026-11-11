"""Create the local dev user. Safe to run repeatedly.

    cd backend && python scripts/seed_dev_user.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.logging import configure_logging  # noqa: E402
from app.core.seed import seed_dev_user  # noqa: E402

if __name__ == "__main__":
    configure_logging()
    seed_dev_user()
