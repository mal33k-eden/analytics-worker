import logging
import os
import subprocess
import threading
import time
from fastapi import FastAPI
from sqlmodel import Session

from app.route_main import api_router
from app.core.config import settings
from app.core.db import engine, init_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(api_router, prefix=settings.API_V1_STR)

worker_process = None
beat_process = None


# Create a function to stream process output to logger
def log_stream(stream, prefix, log_level=logging.INFO):
    """Stream subprocess output to logger."""
    for line in iter(stream.readline, ''):
        if not line:
            break
        line = line.rstrip()
        if "ERROR" in line or "Error" in line or "error" in line:
            logger.error(f"{prefix}: {line}")
        elif "WARNING" in line or "Warning" in line or "warning" in line:
            logger.warning(f"{prefix}: {line}")
        else:
            logger.log(log_level, f"{prefix}: {line}")


def start_celery_worker():
    global worker_process
    env = os.environ.copy()

    # Set log level to DEBUG for more detailed information
    env["LOGLEVEL"] = "DEBUG"

    # Start Celery worker process with file logging
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    worker_log_file = os.path.join(log_dir, "celery_worker.log")

    try:
        # Start with redirected output
        worker_process = subprocess.Popen(
            [
                "celery", "-A", "app.pipeline.celery_app.celery_app", "worker",
                "--loglevel=DEBUG",  # Set to DEBUG for maximum info
                "-l", "DEBUG",
                "--logfile", worker_log_file  # Save logs to file
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,  # Line buffered
            universal_newlines=True  # Text mode
        )

        logger.info(f"Celery worker started. Logs available at {worker_log_file}")

        # Start threads to stream output to logger
        worker_stdout_thread = threading.Thread(
            target=log_stream,
            args=(worker_process.stdout, "Celery Worker")
        )
        worker_stdout_thread.daemon = True
        worker_stdout_thread.start()

        worker_stderr_thread = threading.Thread(
            target=log_stream,
            args=(worker_process.stderr, "Celery Worker Error", logging.ERROR)
        )
        worker_stderr_thread.daemon = True
        worker_stderr_thread.start()

    except Exception as err:
        logger.error(f"Error starting celery worker: {err}")


def start_celery_beat():
    global beat_process
    env = os.environ.copy()

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    beat_log_file = os.path.join(log_dir, "celery_beat.log")

    # Start Celery beat process with file logging
    try:
        beat_process = subprocess.Popen(
            [
                "celery", "-A", "app.pipeline.celery_app.celery_app", "beat",
                "--loglevel=DEBUG",
                "--logfile", beat_log_file  # Save logs to file
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,  # Line buffered
            universal_newlines=True  # Text mode
        )

        logger.info(f"Celery beat started. Logs available at {beat_log_file}")

        # Start threads to stream output to logger
        beat_stdout_thread = threading.Thread(
            target=log_stream,
            args=(beat_process.stdout, "Celery Beat")
        )
        beat_stdout_thread.daemon = True
        beat_stdout_thread.start()

        beat_stderr_thread = threading.Thread(
            target=log_stream,
            args=(beat_process.stderr, "Celery Beat Error", logging.ERROR)
        )
        beat_stderr_thread.daemon = True
        beat_stderr_thread.start()

    except Exception as err:
        logger.error(f"Error starting celery beat: {err}")


@app.on_event("startup")
def on_startup():
    # Create a session to pass to init_db
    with Session(engine) as session:
        init_db(session)

    # Start Celery worker in a separate thread
    worker_thread = threading.Thread(target=start_celery_worker)
    worker_thread.daemon = True  # Thread will exit when main thread exits
    worker_thread.start()

    # Start Celery beat in a separate thread
    beat_thread = threading.Thread(target=start_celery_beat)
    beat_thread.daemon = True
    beat_thread.start()

    logger.info("Celery worker and beat scheduler started")


# Health check endpoint
@app.get("/health")
async def health_check():
    # Check if Celery processes are running
    worker_status = "running" if worker_process and worker_process.poll() is None else "stopped"
    beat_status = "running" if beat_process and beat_process.poll() is None else "stopped"

    # Add log file paths to the response
    log_dir = os.path.join(os.getcwd(), "logs")
    worker_log = os.path.join(log_dir, "celery_worker.log")
    beat_log = os.path.join(log_dir, "celery_beat.log")

    return {
        "status": "healthy",
        "celery_worker": worker_status,
        "celery_beat": beat_status,
        "log_files": {
            "worker_log": worker_log if os.path.exists(worker_log) else None,
            "beat_log": beat_log if os.path.exists(beat_log) else None
        }
    }


# Add a route to view recent logs
@app.get("/logs/{log_type}")
async def get_logs(log_type: str, lines: int = 100):
    """Endpoint to view the last N lines of logs."""
    log_dir = os.path.join(os.getcwd(), "logs")

    if log_type == "worker":
        log_file = os.path.join(log_dir, "celery_worker.log")
    elif log_type == "beat":
        log_file = os.path.join(log_dir, "celery_beat.log")
    else:
        return {"error": "Invalid log type. Use 'worker' or 'beat'"}

    if not os.path.exists(log_file):
        return {"error": f"Log file {log_file} does not exist"}

    try:
        # Use tail-like functionality to get last N lines
        result = subprocess.run(
            ["tail", "-n", str(lines), log_file],
            capture_output=True,
            text=True
        )
        log_content = result.stdout
        return {"content": log_content}
    except Exception as e:
        return {"error": f"Failed to read log file: {str(e)}"}
