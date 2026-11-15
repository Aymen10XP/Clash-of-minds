FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --ingroup app app

COPY server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY manage.py /app/manage.py
COPY server /app/server
COPY accounts /app/accounts
COPY quiz /app/quiz
COPY multiplayer /app/multiplayer

RUN DJANGO_SECRET_KEY=build-only \
    POSTGRES_PASSWORD=build-only \
    python manage.py collectstatic --noinput \
    && mkdir -p /app/media \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["gunicorn", "server.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-"]
