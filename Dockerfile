FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN python -m pip install --upgrade pip
RUN python -m pip install \
    "timesfm[pax]==1.3.0" \
    "yfinance>=0.2.54,<1.0" \
    "pandas>=2.2,<3.0" \
    "numpy>=1.26,<2.0"

COPY src /workspace/src

ENTRYPOINT ["python", "src/run_forecast.py"]
