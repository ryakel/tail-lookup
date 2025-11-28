FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY data/aircraft.db ./data/aircraft.db

ENV PYTHONPATH=/app/app
ENV DB_PATH=/app/data/aircraft.db

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/api/v1/health').raise_for_status()"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
