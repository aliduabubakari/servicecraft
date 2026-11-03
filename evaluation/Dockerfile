FROM python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9
LABEL org.opencontainers.image.title="ServiceCraft Dagster evaluation runtime"
COPY requirements-evaluation.lock /opt/evaluator/requirements.txt
RUN pip install --no-cache-dir -r /opt/evaluator/requirements.txt && pip freeze > /opt/evaluator/packages.txt
COPY app/runtime_worker.py /opt/evaluator/runtime_worker.py
COPY app/static_analysis.py /opt/evaluator/static_analysis.py
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp DAGSTER_HOME=/tmp/dagster
USER 65532:65532
CMD ["python", "/opt/evaluator/runtime_worker.py"]
