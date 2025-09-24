FROM python:3.11-slim

# System deps for pdf parsing and trafilatura
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libxml2 libxslt1.1 libxslt1-dev libffi-dev \
    libjpeg62-turbo-dev poppler-utils curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY README.md .
ENV PYTHONPATH=/app
ENV ARTIFACTS_DIR=/work/artifacts
RUN mkdir -p /work/artifacts /app/docs/summaries

EXPOSE 8000
ENTRYPOINT ["python", "app/main.py", "--serve"]
