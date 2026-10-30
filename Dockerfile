# Playwright base ships Chromium + all system deps. Pin to your playwright version.
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

RUN apt-get update && apt-get install -y --no-install-recommends \
        xvfb cron tini curl sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data/imgs/variants

ENV FBM_PROFILE=/app/data/fb_profile \
    FBM_DB=/app/data/fbm.sqlite \
    FBM_STATE=/app/data/fbm_state.json \
    FBM_SELECTORS=/app/data/selectors.json \
    DISPLAY=:99 \
    PYTHONUNBUFFERED=1

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
CMD ["worker"]