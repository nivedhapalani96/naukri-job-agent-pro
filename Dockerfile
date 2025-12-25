FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY job_agent job_agent
COPY config config
COPY pyproject.toml pyproject.toml
COPY README.md README.md

RUN mkdir -p /app/data
CMD ["python", "-m", "job_agent.cli", "run", "--config", "config/config.yaml"]
