"""Entry point:  cd backend && python -m app.worker"""
import logging
import signal
import threading


def main() -> None:
    from app.core.config import get_settings
    from app.core.logging import configure_logging
    from app.db.session import SessionLocal
    from app.storage import get_storage
    from app.worker.loop import Worker, WorkerConfig

    configure_logging()
    settings = get_settings()
    stop = threading.Event()

    def request_stop(signum, _frame):
        logging.getLogger("keychord.worker").info("signal %s received; finishing up", signum)
        stop.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    Worker(SessionLocal, get_storage(), WorkerConfig.from_settings(settings)).run_forever(stop)


if __name__ == "__main__":  # the guard is required: the "spawn" start method re-imports this module in each child
    main()
