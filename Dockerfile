FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src /app/src
COPY alembic.ini /app/alembic.ini
COPY pyproject.toml /app/pyproject.toml

EXPOSE 8000
CMD ["uvicorn", "documind.app:app", "--host", "0.0.0.0", "--port", "8000"]
