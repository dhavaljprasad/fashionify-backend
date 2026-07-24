from celery import Celery
from app.config.variables import ConfigVariables
from dotenv import load_dotenv
import os

loaded = load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

celery_app = Celery(
    "worker",
    broker=ConfigVariables.REDIS_URL,
    backend=ConfigVariables.REDIS_URL,
)

celery_app.conf.update(
    task_track_started=True,
    timezone="Asia/Kolkata",
)

celery_app.autodiscover_tasks(["app.workers.tasks"])
