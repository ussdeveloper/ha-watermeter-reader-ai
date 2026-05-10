# HA Watermeter Reader AI

Add-on Home Assistanta, ktory zastępuje n8n OCR flow:

- pobiera obraz z konfigurowalnego URL
- opcjonalnie odpala URL przygotowujacy capture
- wysyla obraz do konfigurowalnego Ollama
- publikuje MQTT discovery i stan do HA
- wystawia HTTP API do ręcznego skanu
- odświeża stan przy starcie i cyklicznie

## Dlaczego tak

To jest bezposredni, samodzielny odpowiednik flow z n8n. Zachowuje te same MQTT topic’i i te same `unique_id`, wiec obecne encje w HA moga zostac bez zmian.

## Domyslne wartosci

Aktualny model OCR:

- `qwen2.5vl:3b`

Domyslne adresy sa ustawione pod obecne srodowisko, ale wszystko jest konfigurowalne w opcjach add-onu.

## GitHub

Repo docelowe:

- `https://github.com/ussdeveloper/ha-watermeter-reader-ai`

## Start

1. Dodaj repozytorium do Home Assistanta.
2. Ustaw adres kamery, adres Ollama i dane MQTT.
3. Wylacz stary flow w n8n, zeby nie publikowal tych samych topicow.
