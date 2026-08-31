# A11oy Factory — governed AI distribution compiler and fail-closed cells.
FROM python:3.14-slim@sha256:cae66f2ef0ec51a9891263eeee7f987dacf0a9879e8aa9353d5606e0530619a5

LABEL org.opencontainers.image.title="A11oy Factory" \
      org.opencontainers.image.description="Governed AI distribution compiler: deterministic locks, policy, SBOM, provenance, receipts." \
      org.opencontainers.image.source="https://github.com/szl-holdings/a11oy-factory" \
      org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

RUN groupadd --system --gid 10001 a11oy \
    && useradd --system --uid 10001 --gid a11oy --home-dir /nonexistent --shell /usr/sbin/nologin a11oy

COPY --chown=10001:10001 a11oy_factory ./a11oy_factory
COPY --chown=10001:10001 factory ./factory
COPY --chown=10001:10001 space/server.py ./server.py
COPY --chown=10001:10001 space/index.html ./index.html

USER 10001:10001
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','7860')+'/healthz', timeout=3).read()"]

CMD ["python", "-u", "server.py"]
