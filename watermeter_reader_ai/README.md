# Watermeter Reader AI Add-on

## What It Does

- Downloads an image from `camera_prepare_url` and `camera_image_url`
- Waits for `camera_settle_seconds` after the prepare step
- Sends the image to Ollama for OCR
- Publishes MQTT discovery data and state
- Exposes an HTTP API for manual scans
- Keeps the main reading entity unchanged when OCR marks a reading as suspicious
- Exposes diagnostic state for the current scan status and raw OCR output
- Exposes the last OCR candidate and image hash for easier Home Assistant debugging
- Rejects concurrent scan requests while a scan is already running

## API

- `GET /health`
- `GET /state`
- `GET /scan`
- `POST /scan`

## Note

If an older automation or workflow is still publishing to the same MQTT topics, both publishers may conflict.
