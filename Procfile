web: uvicorn app.main:app --host=0.0.0.0 --port=$PORT
worker: python -m playwright install chromium && celery -A app.workers.celery:celery_app worker --loglevel=info --pool=solo