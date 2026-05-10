FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION=0.1.0

LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="addon" \
      io.hass.arch="amd64|aarch64"

RUN apk add --no-cache python3 py3-pip ca-certificates

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/app.py
COPY run.sh /run.sh

RUN chmod a+x /run.sh

CMD ["/run.sh"]
