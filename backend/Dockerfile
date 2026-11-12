FROM python:3.12.15-slim@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2 AS builder
WORKDIR /app
RUN pip install uv==0.13.7
COPY pyproject.toml uv.lock ./
COPY alembic.ini ./
COPY modules/ ./modules/
RUN uv sync --frozen --no-dev

FROM python:3.12.15-slim@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/alembic.ini ./
COPY --from=builder /app/modules/ ./modules/
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh
RUN groupadd -r medhub && useradd -r -g medhub medhub
USER medhub
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["./entrypoint.sh"]
# --forwarded-allow-ips= (empty): the server never rewrites the TCP peer; the application applies
# the trusted-proxy rule once (SR-042, ADR-0019). A Compose `command:` replaces this CMD.
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--forwarded-allow-ips=", "app.main:app"]
