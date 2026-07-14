FROM python:3.12-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive PATH="/root/.local/bin:/usr/local/bin:${PATH}"
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates chromium curl ffmpeg fluxbox git jq novnc websockify x11vnc xvfb fonts-liberation procps tini && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://claude.ai/install.sh | bash -s stable && curl -fsSL https://saveto.spotify.com/install.sh | bash -s -- --dir /usr/local/bin --no-skills
WORKDIR /workspace
COPY cloud/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . /workspace
RUN chmod +x /workspace/cloud/scripts/entrypoint.sh
WORKDIR /workspace/cloud
ENTRYPOINT ["/usr/bin/tini","--","/workspace/cloud/scripts/entrypoint.sh"]
CMD ["python","runner.py","api"]
