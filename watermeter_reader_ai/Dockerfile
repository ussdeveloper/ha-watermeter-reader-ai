ARG BUILD_FROM=ghcr.io/home-assistant/base:3.23
FROM ${BUILD_FROM}

ARG BUILD_VERSION=0.2.1

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

CMD ["/run.sh"]
