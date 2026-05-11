# HA Watermeter Reader AI

Home Assistant add-on for reading a water meter image with Ollama and publishing the result over MQTT.

- Downloads an image from configurable URLs
- Optionally triggers a capture URL before reading
- Sends the image to a configurable Ollama server
- Publishes MQTT discovery data and state to Home Assistant
- Exposes an HTTP API for manual scans
- Refreshes state on startup and on a schedule

## Defaults

Default OCR model:

- `qwen2.5vl:3b`

Repository defaults are intentionally anonymized. Configure your actual camera, Ollama, and MQTT settings in the add-on options.

## GitHub

- `https://github.com/ussdeveloper/ha-watermeter-reader-ai`

## Setup

1. Add the repository to Home Assistant.
2. Configure the camera, Ollama, and MQTT settings.
3. Disable any older publisher that uses the same MQTT topics.
