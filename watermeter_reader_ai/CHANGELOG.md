# Changelog

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
