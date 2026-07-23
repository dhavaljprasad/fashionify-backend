from celery import Celery
from app.config.variables import ConfigVariables

celery_app = Celery(
    "worker",
    broker=ConfigVariables.REDIS_URL,
    backend=ConfigVariables.REDIS_URL,
)

if ConfigVariables.ENVIRONMENT == "production":
    celery_app.conf.broker_use_ssl = {
        "ssl_cert_reqs": "CERT_NONE",
    }
    celery_app.conf.redis_backend_use_ssl = {
        "ssl_cert_reqs": "CERT_NONE",
    }

celery_app.conf.update(
    task_track_started=True,
    timezone="Asia/Kolkata",
)

celery_app.autodiscover_tasks(["app.workers.tasks"])
