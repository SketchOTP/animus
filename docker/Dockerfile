FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY hermes-agent /opt/hermes-agent
RUN pip install --no-cache-dir -e /opt/hermes-agent || true

COPY animus-chat/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt

COPY animus-chat/ /app/animus-chat/
WORKDIR /app/animus-chat

RUN mkdir -p /data
ENV DATA_DIR=/data
ENV CHAT_HOST=0.0.0.0
ENV CHAT_PORT=3001
ENV HERMES_AGENT_DIR=/opt/hermes-agent

EXPOSE 3001

CMD ["python", "server.py"]
