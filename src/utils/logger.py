# Project: braintransplant-ai — File: src/utils/logger.py
import os
import logging
import threading

# ---- Explicit constants (no defaults) ----
LOG_DIR = "/app/outputs/logs"
LOG_FILE = "braintransplant.log"

# Internal singleton state
_lock = threading.Lock()
_initialized = False

def get_logger(name: str = "btai") -> logging.Logger:
    """
    Return a process-wide logger that writes to one file:
        /app/outputs/logs/braintransplant.log
    Idempotent: safe to call from any module.
    """
    global _initialized
    with _lock:
        os.makedirs(LOG_DIR, exist_ok=True)
        logger = logging.getLogger(name)

        if not _initialized:
            logger.setLevel(logging.INFO)
            fh = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE), encoding="utf-8")
            fh.setLevel(logging.INFO)
            fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
            fh.setFormatter(fmt)
            # Attach to root so child loggers (btai.ui, btai.rag, btai.admin, etc.) share the handler
            root = logging.getLogger()
            if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == fh.baseFilename
                       for h in root.handlers):
                root.addHandler(fh)
                root.setLevel(logging.INFO)
            _initialized = True

        # Ensure child loggers propagate to root handler
        logger.propagate = True
        return logger
