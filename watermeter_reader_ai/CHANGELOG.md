# Changelog

## 0.3.3

- shorten the published OCR image fingerprint so the Home Assistant diagnostic entity fits cleanly in the UI

## 0.3.2

- reduce false suspicious readings for short test intervals and add configurable suspicious-reading thresholds
- add cache-busting camera fetches plus diagnostic entities for the last OCR candidate and last image hash

## 0.3.1

- add diagnostic entities for the current scan state and raw OCR output
- reject concurrent scan requests while a scan is already running

## 0.3.0

- replace the single OCR prompt with editable primary and retry prompt templates plus placeholder expansion

## 0.2.11

- correct the drum transition guidance so new digits are described as appearing from the bottom

## 0.2.10

- version bump to provide a fresh Home Assistant update target after a Supervisor-side update failure

## 0.2.9

- add optional OCR context from the last confirmed reading and a second OCR pass for suspicious results

## 0.2.8

- persist the accepted meter reading and septic baseline in `/data` so add-on updates do not reset them

## 0.2.7

- add a Home Assistant camera entity for the exact last image frame sent to OCR

## 0.2.6

- translate repository docs and user-facing strings to English
- anonymize default repository configuration values while keeping the default model name
- add Home Assistant option descriptions via English translations

## 0.2.5

- version bump to provide a fresh Home Assistant update path

## 0.2.4

- pass the last confirmed reading and drum-meter guidance into the OCR prompt as a soft hint

## 0.2.3

- add a refresh reading button and a confirmed reading override control for the main water meter state

## 0.2.2

- change the default device manufacturer/config label from n8n to ai-watermeter

## 0.2.1

- change the default Home Assistant device name to ai-watermeter so it is separate from the old n8n flow device
- keep the last valid reading when OCR looks suspicious and expose a separate last reading status entity

## 0.2.0

- remove the MQTT disconnect callback and simplify the startup script to avoid Supervisor startup issues

## 0.1.9

- switch to the official Home Assistant base image and disable init for Supervisor compatibility

## 0.1.8

- publish under a new image name to avoid stale image reuse in Home Assistant

## 0.1.7

- version bump to trigger a fresh add-on update

## 0.1.6

- fix MQTT disconnect callback compatibility and honor configured API port

## 0.1.5

- restore a shell wrapper so Supervisor can still find /run.sh if it expects it

## 0.1.4

- add a real web UI and start HTTP independently from MQTT

## 0.1.3

- run the app directly with python to avoid startup script issues

## 0.1.2

- fix startup script so the add-on runs on the Alpine base image

## 0.1.0

- initial release
- MQTT discovery/state replacement for n8n flow
- Ollama OCR with configurable model and image URL
