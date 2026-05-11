import base64
import json
import os
import re
import signal
import threading
import time
from dataclasses import dataclass, asdict
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from typing import Any

import paho.mqtt.client as mqtt
import requests


def env(name: str, default: Any = None):
    return os.getenv(name, default)


def load_options() -> dict[str, Any]:
    options_path = Path("/data/options.json")
    if not options_path.exists():
        return {}
    try:
        return json.loads(options_path.read_text())
    except Exception:
        return {}


OPTIONS = load_options()


def cfg(name: str, default: Any = None):
    if name in OPTIONS:
        value = OPTIONS[name]
    else:
        value = env(name.upper(), default)
    if isinstance(default, bool):
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on"}
    if isinstance(default, int):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    return value


@dataclass
class State:
    modeName: str | None = None
    reading: str | None = None
    last_reading_status: str = "unknown"
    suspicious: bool = False
    warning: str | None = None
    deltaM3: float | None = None
    rateM3PerHour: float | None = None
    last_reading_timestamp: int | None = None
    captured_septic_baseline: float | None = None
    captured_septic_timestamp: int | None = None
    captured_septic_source: str | None = None
    septic_level: float | None = None
    action: str | None = None
    action_value: float | None = None
    ocr_raw: str | None = None


class WatermeterReader:
    def __init__(self):
        self.camera_prepare_url = cfg("camera_prepare_url", "")
        self.camera_image_url = cfg("camera_image_url", "")
        self.camera_settle_seconds = cfg("camera_settle_seconds", 2)
        self.ollama_url = cfg("ollama_url", "http://127.0.0.1:11434")
        self.ollama_model = cfg("ollama_model", "qwen2.5vl:3b")
        self.ocr_prompt = cfg(
            "ocr_prompt",
            "Read the water meter display. Return exactly 8 digits only, no unit, no spaces, no commas, no explanation. Preserve leading zeros.",
        )
        self.scan_interval_minutes = cfg("scan_interval_minutes", 30)
        self.startup_scan = cfg("startup_scan", True)
        self.mqtt_host = cfg("mqtt_host", "127.0.0.1")
        self.mqtt_port = cfg("mqtt_port", 1883)
        self.mqtt_username = cfg("mqtt_username", "")
        self.mqtt_password = cfg("mqtt_password", "")
        self.mqtt_base_topic = cfg("mqtt_base_topic", "n8n/watermeter")
        self.mqtt_septic_topic_prefix = cfg("mqtt_septic_topic_prefix", "n8n/septic")
        self.mqtt_discovery_prefix = cfg("mqtt_discovery_prefix", "homeassistant")
        self.mqtt_device_identifier = cfg("mqtt_device_identifier", "ai_watermeter")
        self.mqtt_device_name = cfg("mqtt_device_name", "ai-watermeter")
        self.mqtt_device_manufacturer = cfg("mqtt_device_manufacturer", "ai-watermeter")
        self.mqtt_device_model = cfg("mqtt_device_model", "OCR watermeter")
        self.api_bind = cfg("api_bind", "0.0.0.0")
        self.api_port = cfg("api_port", 8099)
        self.request_timeout_seconds = cfg("request_timeout_seconds", 15)
        self.mqtt_availability_topic = f"{self.mqtt_base_topic}/availability"

        self.state = State()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self.mqtt_username:
            self.mqtt.username_pw_set(self.mqtt_username, self.mqtt_password)
        self.mqtt.on_connect = self._on_mqtt_connect
        self.mqtt.on_message = self._on_mqtt_message

    def device(self):
        return {
            "identifiers": [self.mqtt_device_identifier],
            "name": self.mqtt_device_name,
            "manufacturer": self.mqtt_device_manufacturer,
            "model": self.mqtt_device_model,
        }

    def render_home(self) -> str:
        page = Template(
            """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>$device_name</title>
  <style>
    :root { color-scheme: dark light; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      margin: 0;
      background: #111827;
      color: #e5e7eb;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
      box-sizing: border-box;
    }
    main {
      width: min(960px, 100%);
      background: #1f2937;
      border: 1px solid #374151;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
    }
    .row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
    button {
      appearance: none;
      border: 0;
      border-radius: 10px;
      padding: 12px 16px;
      background: #2563eb;
      color: white;
      font-weight: 700;
      cursor: pointer;
    }
    button:disabled { opacity: 0.6; cursor: progress; }
    code, pre {
      background: #111827;
      border: 1px solid #374151;
      border-radius: 12px;
      padding: 12px;
      overflow: auto;
    }
    pre { margin: 0; white-space: pre-wrap; word-break: break-word; }
    .muted { color: #9ca3af; }
    .status { font-weight: 700; }
  </style>
</head>
<body>
  <main>
    <h1>$device_name</h1>
    <p class="muted">MQTT base topic: <code>$base_topic</code></p>
    <div class="row">
      <button id="scan">Scan now</button>
      <span id="status" class="status">Loading...</span>
    </div>
    <h2>State</h2>
    <pre id="state">Loading...</pre>
    <p class="muted">API: <code>/health</code> <code>/state</code> <code>/scan</code></p>
  </main>
  <script>
    const statusEl = document.getElementById('status');
    const stateEl = document.getElementById('state');
    const scanEl = document.getElementById('scan');

    async function loadState() {
      try {
        const response = await fetch('/state', { cache: 'no-store' });
        const data = await response.json();
        stateEl.textContent = JSON.stringify(data, null, 2);
        statusEl.textContent = data.warning ? 'Warning: ' + data.warning : 'Ready';
      } catch (error) {
        statusEl.textContent = 'Offline';
        stateEl.textContent = String(error);
      }
    }

    async function triggerScan() {
      scanEl.disabled = true;
      statusEl.textContent = 'Scanning...';
      try {
        const response = await fetch('/scan', { method: 'POST' });
        const data = await response.json();
        stateEl.textContent = JSON.stringify(data, null, 2);
        statusEl.textContent = data.warning ? 'Warning: ' + data.warning : 'Scan complete';
      } catch (error) {
        statusEl.textContent = 'Scan failed';
        stateEl.textContent = String(error);
      } finally {
        scanEl.disabled = false;
      }
    }

    scanEl.addEventListener('click', triggerScan);
    loadState();
    setInterval(loadState, 5000);
  </script>
</body>
</html>
"""
        )
        return page.substitute(device_name=escape(self.mqtt_device_name), base_topic=escape(self.mqtt_base_topic))

    def connect_mqtt(self):
        self.mqtt.reconnect_delay_set(min_delay=1, max_delay=30)
        while not self.stop_event.is_set():
            try:
                self.mqtt.connect(self.mqtt_host, self.mqtt_port, 60)
                self.mqtt.loop_start()
                return
            except Exception:
                time.sleep(3)

    def _on_mqtt_connect(self, client, userdata, flags, reason_code, properties=None):
        septic_set = f"{self.mqtt_septic_topic_prefix}/capture/set"
        septic_reset = f"{self.mqtt_septic_topic_prefix}/reset"
        meter_set = f"{self.mqtt_base_topic}/reading/set"
        meter_refresh = f"{self.mqtt_base_topic}/refresh"
        client.subscribe([(septic_set, 0), (septic_reset, 0), (meter_set, 0), (meter_refresh, 0)])
        self.publish_discovery()
        self.publish_availability("online")
        with self.lock:
            has_state = any(
                [
                    self.state.modeName is not None,
                    self.state.reading is not None,
                    self.state.suspicious,
                    self.state.warning is not None,
                    self.state.deltaM3 is not None,
                    self.state.rateM3PerHour is not None,
                    self.state.last_reading_timestamp is not None,
                    self.state.captured_septic_baseline is not None,
                    self.state.captured_septic_timestamp is not None,
                    self.state.captured_septic_source is not None,
                    self.state.septic_level is not None,
                    self.state.action is not None,
                    self.state.action_value is not None,
                    self.state.ocr_raw is not None,
                ]
            )
            state_payload = self.build_payload() if has_state else None
        if state_payload is not None:
            self.publish(f"{self.mqtt_base_topic}/state", state_payload, retain=True)

    def _on_mqtt_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8", "ignore").strip()
        if topic.endswith("/reset"):
            self.handle_reset()
        elif topic.endswith("/refresh"):
            self.scan_once("refresh")
        elif topic.endswith("/reading/set"):
            self.handle_reading_override(payload)
        elif topic.endswith("/capture/set"):
            self.handle_override(payload)

    def publish(self, topic: str, payload: Any, retain: bool = True):
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload, ensure_ascii=False)
        self.mqtt.publish(topic, payload, retain=retain)

    def publish_availability(self, status: str):
        self.publish(self.mqtt_availability_topic, status, retain=True)

    def publish_discovery(self):
        base = self.mqtt_base_topic
        shared = f"{base}/state"
        device = self.device()
        configs = [
            (
                f"{self.mqtt_discovery_prefix}/sensor/{self.mqtt_device_identifier}/config",
                {
                    "name": self.mqtt_device_name,
                    "unique_id": f"{self.mqtt_device_identifier}_reading",
                    "state_topic": shared,
                    "json_attributes_topic": shared,
                    "value_template": "{{ value_json.reading | float }}",
                    "unit_of_measurement": "m³",
                    "state_class": "total_increasing",
                    "device_class": "water",
                    "icon": "mdi:water",
                    "suggested_display_precision": 3,
                    "availability_topic": self.mqtt_availability_topic,
                    "payload_available": "online",
                    "payload_not_available": "offline",
                    "device": device,
                },
            ),
            (
                f"{self.mqtt_discovery_prefix}/sensor/{self.mqtt_device_identifier}_last_reading_timestamp/config",
                {
                    "name": "Last reading timestamp",
                    "unique_id": f"{self.mqtt_device_identifier}_last_reading_timestamp",
                    "default_entity_id": "sensor.ai_watermeter_last_reading_timestamp",
                    "state_topic": shared,
                    "value_template": "{{ as_datetime(value_json.last_reading_timestamp) }}",
                    "device_class": "timestamp",
                    "entity_category": "diagnostic",
                    "availability_topic": self.mqtt_availability_topic,
                    "payload_available": "online",
                    "payload_not_available": "offline",
                    "device": device,
                },
            ),
            (
                f"{self.mqtt_discovery_prefix}/sensor/{self.mqtt_device_identifier}_last_reading_status/config",
                {
                    "name": "Last reading status",
                    "unique_id": f"{self.mqtt_device_identifier}_last_reading_status",
                    "default_entity_id": "sensor.ai_watermeter_last_reading_status",
                    "state_topic": shared,
                    "value_template": "{{ value_json.last_reading_status }}",
                    "entity_category": "diagnostic",
                    "icon": "mdi:clipboard-pulse-outline",
                    "availability_topic": self.mqtt_availability_topic,
                    "payload_available": "online",
                    "payload_not_available": "offline",
                    "device": device,
                },
            ),
            (
                f"{self.mqtt_discovery_prefix}/sensor/{self.mqtt_device_identifier}_septic_level/config",
                {
                    "name": "Szambo level",
                    "unique_id": f"{self.mqtt_device_identifier}_septic_level",
                    "default_entity_id": "sensor.ai_watermeter_septic_level",
                    "state_topic": shared,
                    "value_template": "{{ value_json.septic_level | float }}",
                    "unit_of_measurement": "m³",
                    "state_class": "measurement",
                    "device_class": "water",
                    "icon": "mdi:water-percent",
                    "suggested_display_precision": 3,
                    "availability_topic": self.mqtt_availability_topic,
                    "payload_available": "online",
                    "payload_not_available": "offline",
                    "device": device,
                },
            ),
            (
                f"{self.mqtt_discovery_prefix}/number/{self.mqtt_device_identifier}_reading_override/config",
                {
                    "name": "Confirmed reading",
                    "unique_id": f"{self.mqtt_device_identifier}_reading_override",
                    "default_entity_id": "number.ai_watermeter_confirmed_reading",
                    "state_topic": shared,
                    "value_template": "{{ value_json.reading | float(0) }}",
                    "command_topic": f"{self.mqtt_base_topic}/reading/set",
                    "unit_of_measurement": "m³",
                    "min": 0,
                    "max": 999999.999,
                    "step": 0.001,
                    "mode": "box",
                    "entity_category": "config",
                    "icon": "mdi:counter",
                    "availability_topic": self.mqtt_availability_topic,
                    "payload_available": "online",
                    "payload_not_available": "offline",
                    "device": device,
                },
            ),
            (
                f"{self.mqtt_discovery_prefix}/button/{self.mqtt_device_identifier}_refresh_reading/config",
                {
                    "name": "Refresh reading",
                    "unique_id": f"{self.mqtt_device_identifier}_refresh_reading",
                    "default_entity_id": "button.ai_watermeter_refresh_reading",
                    "command_topic": f"{self.mqtt_base_topic}/refresh",
                    "payload_press": "refresh",
                    "entity_category": "config",
                    "icon": "mdi:refresh",
                    "availability_topic": self.mqtt_availability_topic,
                    "payload_available": "online",
                    "payload_not_available": "offline",
                    "device": device,
                },
            ),
            (
                f"{self.mqtt_discovery_prefix}/number/{self.mqtt_device_identifier}_septic_capture_level/config",
                {
                    "name": "Capture szambo level",
                    "unique_id": f"{self.mqtt_device_identifier}_septic_capture_level",
                    "default_entity_id": "number.ai_watermeter_septic_capture_level",
                    "state_topic": shared,
                    "value_template": "{{ value_json.captured_septic_baseline | float }}",
                    "command_topic": f"{self.mqtt_septic_topic_prefix}/capture/set",
                    "unit_of_measurement": "m³",
                    "min": 0,
                    "max": 999999.999,
                    "step": 0.001,
                    "mode": "box",
                    "entity_category": "config",
                    "icon": "mdi:counter",
                    "availability_topic": self.mqtt_availability_topic,
                    "payload_available": "online",
                    "payload_not_available": "offline",
                    "device": device,
                },
            ),
            (
                f"{self.mqtt_discovery_prefix}/button/{self.mqtt_device_identifier}_septic_reset_level/config",
                {
                    "name": "Reset szambo level",
                    "unique_id": f"{self.mqtt_device_identifier}_septic_reset_level",
                    "default_entity_id": "button.ai_watermeter_septic_reset_level",
                    "command_topic": f"{self.mqtt_septic_topic_prefix}/reset",
                    "payload_press": "reset",
                    "entity_category": "config",
                    "icon": "mdi:restore",
                    "availability_topic": self.mqtt_availability_topic,
                    "payload_available": "online",
                    "payload_not_available": "offline",
                    "device": device,
                },
            ),
        ]
        for topic, payload in configs:
            self.publish(topic, payload, retain=True)

    def prepare_image(self):
        if self.camera_prepare_url:
            requests.get(self.camera_prepare_url, timeout=self.request_timeout_seconds)
            if self.camera_settle_seconds > 0:
                time.sleep(self.camera_settle_seconds)

    def fetch_image(self) -> bytes:
        resp = requests.get(self.camera_image_url, timeout=self.request_timeout_seconds)
        resp.raise_for_status()
        return resp.content

    def ocr(self, image_bytes: bytes) -> tuple[str, str]:
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        payload = {
            "model": self.ollama_model,
            "messages": [
                {
                    "role": "user",
                    "content": self.ocr_prompt,
                    "images": [image_b64],
                }
            ],
            "stream": False,
        }
        resp = requests.post(f"{self.ollama_url.rstrip('/')}/api/chat", json=payload, timeout=self.request_timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content") or data.get("content") or ""
        return content, self.ollama_model

    @staticmethod
    def normalize_reading(raw: str) -> str | None:
        digits = re.sub(r"\s*m(?:3|³)\s*$", "", raw, flags=re.I)
        digits = re.sub(r"[^0-9]", "", digits)
        if not digits:
            return None
        normalized = digits.zfill(8)[-8:]
        return f"{normalized[:5]}.{normalized[5:]}"

    def build_payload(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        extra = extra or {}
        septic_level = None
        if self.state.reading is not None and self.state.captured_septic_baseline is not None:
            septic_level = round(float(self.state.reading) - float(self.state.captured_septic_baseline), 3)
        payload = asdict(self.state)
        payload["modeName"] = self.state.modeName or self.ollama_model
        payload["septic_level"] = septic_level
        payload.update(extra)
        return payload

    def update_state(self, reading: str | None, raw_ocr: str, mode_name: str, action: str = "ocr", suspicious: bool = False, warning: str | None = None):
        now = int(time.time())
        with self.lock:
            previous = float(self.state.reading) if self.state.reading is not None else None
            current = float(reading) if reading is not None else None
            previous_reading = self.state.reading
            accepted_reading = reading
            delta = None
            rate = None
            if current is not None and previous is not None and self.state.last_reading_timestamp is not None:
                delta = round(current - previous, 3)
                hours = max((now - self.state.last_reading_timestamp) / 3600.0, 1 / 3600.0)
                rate = round(abs(delta) / hours, 3)
                if delta < 0:
                    suspicious = True
                    warning = warning or f"Odczyt spadl o {abs(delta):.3f} m3. To wyglada na blad OCR."
                elif rate > 1:
                    suspicious = True
                    warning = warning or f"Podejrzana zmiana: {delta:.3f} m3 w {hours:.2f} h. Mozliwy blad OCR."

            baseline_for_check = self.state.captured_septic_baseline
            if baseline_for_check is not None and current is not None:
                septic_level = round(current - float(baseline_for_check), 3)
                if septic_level < 0:
                    suspicious = True
                    warning = warning or "Szambo level jest ponizej captured baseline."

            if suspicious:
                accepted_reading = previous_reading
            status = "suspicious" if suspicious else "ok"

            self.state.modeName = mode_name
            self.state.reading = accepted_reading
            self.state.last_reading_status = status
            self.state.suspicious = suspicious
            self.state.warning = warning
            self.state.deltaM3 = delta
            self.state.rateM3PerHour = rate
            self.state.last_reading_timestamp = now
            self.state.action = action
            self.state.action_value = current
            self.state.ocr_raw = raw_ocr
            if self.state.captured_septic_baseline is None and current is not None and not suspicious:
                self.state.captured_septic_baseline = current
                self.state.captured_septic_timestamp = now
                self.state.captured_septic_source = "auto"

            state_payload = self.build_payload()

        self.publish(f"{self.mqtt_base_topic}/state", state_payload, retain=True)
        return state_payload

    def handle_override(self, payload: str):
        try:
            baseline = float(payload)
        except ValueError:
            return self.build_payload({"action": "override", "warning": f"Nieprawidlowa wartosc override: {payload!r}"})
        with self.lock:
            self.state.captured_septic_baseline = baseline
            self.state.captured_septic_timestamp = int(time.time())
            self.state.captured_septic_source = "override"
        state_payload = self.build_payload({"action": "override", "action_value": baseline})
        self.publish(f"{self.mqtt_base_topic}/state", state_payload, retain=True)
        return state_payload

    def handle_reset(self):
        with self.lock:
            if self.state.reading is None:
                return self.build_payload({"action": "reset", "warning": "Brak ostatniego poprawnego odczytu, nie moge zresetowac szamba."})
            baseline = float(self.state.reading)
            self.state.captured_septic_baseline = baseline
            self.state.captured_septic_timestamp = int(time.time())
            self.state.captured_septic_source = "reset"
        state_payload = self.build_payload({"action": "reset", "action_value": baseline})
        self.publish(f"{self.mqtt_base_topic}/state", state_payload, retain=True)
        return state_payload

    def handle_reading_override(self, payload: str):
        try:
            confirmed = round(float(payload), 3)
        except ValueError:
            return self.build_payload({"action": "reading_override", "warning": f"Nieprawidlowa wartosc odczytu: {payload!r}"})
        with self.lock:
            now = int(time.time())
            self.state.reading = f"{confirmed:.3f}"
            self.state.last_reading_status = "ok"
            self.state.suspicious = False
            self.state.warning = None
            self.state.deltaM3 = None
            self.state.rateM3PerHour = None
            self.state.last_reading_timestamp = now
            self.state.action = "reading_override"
            self.state.action_value = confirmed
            self.state.ocr_raw = None
        state_payload = self.build_payload({"action": "reading_override", "action_value": confirmed})
        self.publish(f"{self.mqtt_base_topic}/state", state_payload, retain=True)
        return state_payload

    def scan_once(self, reason: str = "manual"):
        try:
            self.prepare_image()
            image = self.fetch_image()
            raw, mode = self.ocr(image)
            reading = self.normalize_reading(raw)
            if reading is None:
                payload = self.update_state(None, raw.strip(), mode, action=reason, suspicious=True, warning="Brak cyfr w odczycie OCR")
            else:
                payload = self.update_state(reading, raw.strip(), mode, action=reason)
            return payload
        except Exception as err:
            warning = f"{type(err).__name__}: {err}"
            with self.lock:
                self.state.modeName = self.ollama_model
                self.state.last_reading_status = "error"
                self.state.suspicious = True
                self.state.warning = warning
                self.state.action = reason
                self.state.ocr_raw = None
            payload = self.build_payload({"warning": warning, "action": reason})
            self.publish(f"{self.mqtt_base_topic}/state", payload, retain=True)
            return payload

    def serve_http(self):
        reader = self

        class Handler(BaseHTTPRequestHandler):
            def _send_json(self, code: int, payload: dict[str, Any]):
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_html(self, code: int, body: str):
                data = body.encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, format, *args):
                return

            def do_GET(self):
                if self.path in {"/", "/index.html"}:
                    self._send_html(200, reader.render_home())
                    return
                if self.path == "/health":
                    self._send_json(200, {"ok": True})
                    return
                if self.path == "/state":
                    self._send_json(200, reader.build_payload())
                    return
                if self.path == "/scan":
                    self._send_json(200, reader.scan_once("api"))
                    return
                self._send_json(404, {"error": "not_found"})

            def do_POST(self):
                if self.path == "/scan":
                    self._send_json(200, reader.scan_once("api"))
                    return
                self._send_json(404, {"error": "not_found"})

        server = ThreadingHTTPServer((self.api_bind, self.api_port), Handler)
        server.timeout = 1
        while not self.stop_event.is_set():
            server.handle_request()

    def schedule_loop(self):
        interval = max(1, int(self.scan_interval_minutes)) * 60
        next_run = time.monotonic() + interval
        while not self.stop_event.is_set():
            if time.monotonic() >= next_run:
                self.scan_once("schedule")
                next_run = time.monotonic() + interval
            time.sleep(1)

    def run(self):
        def shutdown(*_args):
            self.stop_event.set()
            try:
                self.publish_availability("offline")
            except Exception:
                pass
            try:
                self.mqtt.loop_stop()
            except Exception:
                pass
            try:
                self.mqtt.disconnect()
            except Exception:
                pass

        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)

        threads = [
            threading.Thread(target=self.serve_http, daemon=True),
            threading.Thread(target=self.schedule_loop, daemon=True),
            threading.Thread(target=self.connect_mqtt, daemon=True),
        ]
        for thread in threads:
            thread.start()

        if self.startup_scan:
            threading.Thread(target=lambda: self.scan_once("startup"), daemon=True).start()

        while not self.stop_event.is_set():
            time.sleep(1)


if __name__ == "__main__":
    WatermeterReader().run()
