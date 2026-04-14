FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

COPY requirements.inference.txt /workspace/requirements.inference.txt

RUN python -m pip install --upgrade pip
RUN python -m pip install \
    "timesfm[pax]==1.3.0" \
    -r /workspace/requirements.inference.txt

COPY src /workspace/src

ENTRYPOINT ["python", "src/run_forecast.py"]
