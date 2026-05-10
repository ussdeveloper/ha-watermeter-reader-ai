# Watermeter Reader AI Add-on

## Co robi

- pobiera obraz z `camera_prepare_url` i `camera_image_url`
- czeka `camera_settle_seconds` po przygotowaniu capture
- wysyla obraz do Ollama
- publikuje MQTT discovery i stan
- wystawia HTTP API do recznego skanu

## Kompatybilnosc

Add-on publikuje te same topic’i co poprzedni flow n8n:

- `homeassistant/sensor/n8n_watermeter/config`
- `homeassistant/sensor/n8n_watermeter_last_reading_timestamp/config`
- `homeassistant/sensor/n8n_septic_level/config`
- `homeassistant/number/n8n_septic_capture_level/config`
- `homeassistant/button/n8n_septic_reset_level/config`
- `n8n/watermeter/state`
- `n8n/watermeter/availability`
- `n8n/septic/capture/set`
- `n8n/septic/reset`

## API

- `GET /health`
- `GET /state`
- `GET /scan`
- `POST /scan`

## Uwaga

Jesli stary workflow n8n zostanie aktywny razem z addonem, oba beda publikowac te same topic’i.
