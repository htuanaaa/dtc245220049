FROM python:3.11-slim

RUN groupadd -g 1000 servergroup && \
    useradd -u 1000 -g servergroup -s /bin/sh -m serveruser

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=serveruser:servergroup . .

USER serveruser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]