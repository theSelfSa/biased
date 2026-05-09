FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
  'fastapi>=0.120.0' \
  'pydantic-settings>=2.11.0' \
  'python-multipart>=0.0.20' \
  'duckdb>=1.4.2' \
  'polars>=1.34.0' \
  'openpyxl>=3.1.5' \
  'psycopg[binary]>=3.2.12' \
  'uvicorn>=0.38.0'

COPY apps/api/src /app/src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
