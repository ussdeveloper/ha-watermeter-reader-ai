FROM alpine:3.20

ARG BUILD_VERSION=0.1.5

LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="addon" \
      io.hass.arch="amd64|aarch64"

RUN apk add --no-cache python3 py3-pip ca-certificates

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/app.py
COPY run.sh /run.sh
ENV PATH="/opt/venv/bin:${PATH}"

RUN chmod a+x /run.sh

CMD ["python3", "-u", "/app/app.py"]
