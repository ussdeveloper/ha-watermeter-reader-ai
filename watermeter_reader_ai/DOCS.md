# Watermeter Reader AI

## Overview

This add-on reads a water meter image with Ollama, publishes MQTT discovery data for Home Assistant, and exposes a small HTTP API and UI.

## Options

### Camera

- `camera_prepare_url`: Optional URL that triggers a fresh still image before OCR.
- `camera_image_url`: URL of the image that should be sent to OCR.
- `camera_settle_seconds`: Delay after the prepare request before the image is downloaded.

### Ollama

- `ollama_url`: Base URL of the Ollama server.
- `ollama_model`: OCR model name. Default: `qwen2.5vl:3b`.
- `ocr_prompt`: Base OCR prompt. The add-on appends extra context about the last confirmed reading and mechanical drum meter behavior.

### Schedule

- `startup_scan`: Run a scan automatically when the add-on starts.
- `scan_interval_minutes`: Periodic scan interval in minutes.

### MQTT

- `mqtt_host`, `mqtt_port`, `mqtt_username`, `mqtt_password`: MQTT connection settings.
- `mqtt_base_topic`: Base topic for water meter state and commands. Default: `ai-watermeter/state`.
- `mqtt_septic_topic_prefix`: Base topic for septic controls. Default: `ai-watermeter/septic`.
- `mqtt_discovery_prefix`: Home Assistant MQTT discovery prefix. Default: `homeassistant`.
- `mqtt_device_identifier`, `mqtt_device_name`, `mqtt_device_manufacturer`, `mqtt_device_model`: Device metadata shown in Home Assistant.
- `Confirmed reading`: Manually sets the accepted water meter reading and becomes the new reference point for suspicious-reading detection.
- `Refresh reading`: Triggers an immediate OCR scan.

### API

- `api_bind`: Bind address for the built-in HTTP server.
- `api_port`: Port for the built-in HTTP server.
- `request_timeout_seconds`: Timeout for camera and Ollama HTTP requests.

## State Payload

State is published on `ai-watermeter/state/state` by default and contains:

- `modeName`
- `reading`
- `last_reading_status`
- `suspicious`
- `warning`
- `deltaM3`
- `rateM3PerHour`
- `last_reading_timestamp`
- `captured_septic_baseline`
- `captured_septic_timestamp`
- `captured_septic_source`
- `septic_level`
- `action`
- `action_value`
- `ocr_raw`

## Home Assistant Entities

- `sensor.ai_watermeter`
- `sensor.ai_watermeter_last_reading_timestamp`
- `sensor.ai_watermeter_last_reading_status`
- `number.ai_watermeter_confirmed_reading`
- `button.ai_watermeter_refresh_reading`
- `sensor.ai_watermeter_septic_level`
- `number.ai_watermeter_septic_capture_level`
- `button.ai_watermeter_septic_reset_level`
