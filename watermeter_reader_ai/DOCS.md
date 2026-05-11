# Watermeter Reader AI

## Opis

Add-on zastępuje OCR flow z n8n. Zachowuje obecne encje HA przez MQTT discovery i uzywa tego samego modelu domyslnie: `qwen2.5vl:3b`.

## Opcje

### Kamera

- `camera_prepare_url`: opcjonalny URL odpalajacy capture/still
- `camera_image_url`: URL obrazu do OCR
- `camera_settle_seconds`: ile poczekac po capture zanim pobierzemy obraz

### Ollama

- `ollama_url`: adres serwera Ollama
- `ollama_model`: model OCR, domyslnie `qwen2.5vl:3b`
- `ocr_prompt`: prompt OCR

### Harmonogram

- `startup_scan`: skan po starcie
- `scan_interval_minutes`: odswiezanie cykliczne

### MQTT

- `mqtt_host`, `mqtt_port`, `mqtt_username`, `mqtt_password`
- `mqtt_base_topic`: domyslnie `n8n/watermeter`
- `mqtt_septic_topic_prefix`: domyslnie `n8n/septic`
- `mqtt_discovery_prefix`: domyslnie `homeassistant`
- `mqtt_device_identifier`, `mqtt_device_name`, `mqtt_device_manufacturer`, `mqtt_device_model`

### API

- `api_bind`
- `request_timeout_seconds`

## Dane wysylane do HA

Stan publikowany na `n8n/watermeter/state` zawiera:

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

## Encje HA

- `sensor.ai_watermeter`
- `sensor.ai_watermeter_last_reading_timestamp`
- `sensor.ai_watermeter_last_reading_status`
- `sensor.ai_watermeter_septic_level`
- `number.ai_watermeter_septic_capture_level`
- `button.ai_watermeter_septic_reset_level`
