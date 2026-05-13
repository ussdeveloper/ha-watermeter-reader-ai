# Watermeter Reader AI

## Overview

This add-on reads a water meter image with Ollama, publishes MQTT discovery data for Home Assistant, and exposes a small HTTP API and UI.

The accepted meter reading, septic baseline, and related timestamps are persisted in `/data/state.json`, so add-on restarts and updates do not clear them.

## Options

### Camera

- `camera_prepare_url`: Optional URL that triggers a fresh still image before OCR.
- `camera_image_url`: URL of the image that should be sent to OCR.
- `camera_settle_seconds`: Delay after the prepare request before the image is downloaded.
- `camera_cache_bust`: Adds a changing query parameter and no-cache headers when the add-on requests a new image.

### Ollama

- `ollama_url`: Base URL of the Ollama server.
- `ollama_model`: OCR model name. Default: `qwen2.5vl:3b`.
- `ocr_prompt_template`: Editable template for the primary OCR prompt.
- `ocr_retry_prompt_template`: Editable template for the second OCR pass when the first result looks suspicious.
- `ocr_include_last_reading_hint`: Adds the last confirmed reading as a soft OCR hint.
- `ocr_retry_on_suspicious`: Runs one extra OCR pass when the first result looks suspicious.
- `suspicious_min_interval_seconds`: Disables the rate-based suspicious check for scans that happen too close together.
- `suspicious_max_rate_m3_per_hour`: Maximum accepted increase rate before a reading is treated as suspicious.
- `suspicious_max_delta_m3`: Maximum accepted single-scan increase before a reading is treated as suspicious.

Template placeholders currently supported:

- `<LAST_CONFIRMED_READING>`
- `<OCR_PROMPT_TEMPLATE>`
- `<PREVIOUS_CANDIDATE>`
- `<RETRY_REASON>`

If a prompt template field is left empty, the add-on falls back to its built-in default template.

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

Concurrent scan requests are not queued. If a scan is already running, the add-on returns the current state with a warning instead of starting a second scan.

## State Payload

State is published on `ai-watermeter/state/state` by default and contains:

- `modeName`
- `reading`
- `current_state`
- `last_image_timestamp`
- `last_image_fingerprint`
- `last_image_sha256`
- `last_candidate_reading`
- `last_reading_status`
- `ocr_attempts`
- `ocr_retry_reason`
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
- `sensor.ai_watermeter_current_state`
- `camera.ai_watermeter_last_ocr_image`
- `sensor.ai_watermeter_last_ocr_image_timestamp`
- `sensor.ai_watermeter_last_ocr_image_sha256`
- `sensor.ai_watermeter_last_ocr_candidate`
- `sensor.ai_watermeter_last_reading_timestamp`
- `sensor.ai_watermeter_last_reading_status`
- `sensor.ai_watermeter_raw_last_read`
- `number.ai_watermeter_confirmed_reading`
- `button.ai_watermeter_refresh_reading`
- `sensor.ai_watermeter_septic_level`
- `number.ai_watermeter_septic_capture_level`
- `button.ai_watermeter_septic_reset_level`
