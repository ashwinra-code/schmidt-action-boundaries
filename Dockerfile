FROM python:3.11-slim

WORKDIR /capsule
COPY . /capsule

RUN pip install --no-cache-dir "numpy>=2.0"

CMD ["bash", "code/run_full_repro.sh", "--strict"]
