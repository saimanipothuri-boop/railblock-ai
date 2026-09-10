"""
REST API & Web Server for RailBlock AI - Indian Railways Automatic Block Planning System.
Uses Python standard library http.server, supporting static frontend and JSON endpoints.
"""
import http.server
import socketserver
import json
import os
import urllib.parse
from dataclasses import asdict
from typing import Dict, Any

from models import MaintenanceBlock, Train, BlockStatus, TrackDirection, Department, TrainCategory
from data import (
    get_default_stations, get_default_sections,
    get_default_trains, get_default_blocks, get_default_assets
)
from optimizer import BlockOptimizer

PORT = 8000
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")


class RailwayState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.stations = get_default_stations()
        self.sections = get_default_sections()
        self.trains = get_default_trains()
        self.blocks = get_default_blocks()
        self.assets = get_default_assets()
        self.optimizer = BlockOptimizer(self.stations, self.sections)
        self.mode = "balanced"
        self.last_kpis = {}
        self.event_logs = [
            {"time": "08:00:00", "type": "INFO", "msg": "System initialized. Corridor HDN-1 (NDLS - CNB) telemetry online."},
            {"time": "08:00:15", "type": "WARNING", "msg": "Critical USFD flaw reported at KM 245.2 (TDL-ETW). High urgency maintenance requested."}
        ]
        # Initial optimization run
        self.run_optimization(self.mode)

    def run_optimization(self, mode: str = "balanced"):
        self.mode = mode
        self.blocks, self.last_kpis = self.optimizer.optimize_all_blocks(self.blocks, self.trains, mode)
        self.event_logs.append({
            "time": "Just now",
            "type": "SUCCESS",
            "msg": f"AI Solver completed block optimization in '{mode}' mode. Saved {self.last_kpis.get('saved_delay_hours', 0)}h of train detention."
        })

    def inject_delay(self, train_no: str, delay_min: int):
        target_train = None
        for t in self.trains:
            if t.train_no == train_no:
                target_train = t
                t.current_delay_min = delay_min
                break

        if target_train:
            self.event_logs.append({
                "time": "Just now",
                "type": "ALERT",
                "msg": f"Dynamic Delay Injected: Train {target_train.train_no} ({target_train.name}) running +{delay_min} mins late."
            })
            # Trigger dynamic AI re-scheduling
            self.blocks, self.last_kpis = self.optimizer.optimize_all_blocks(self.blocks, self.trains, self.mode)
            self.event_logs.append({
                "time": "Just now",
                "type": "AI_REPLAN",
                "msg": f"AI Engine dynamically re-scheduled downstream blocks to absorb Train {target_train.train_no} delay with minimal ripple."
            })


STATE = RailwayState()


class RailwayRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        response_body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/network":
            self._send_json({
                "stations": [asdict(s) for s in STATE.stations],
                "sections": [asdict(sec) for sec in STATE.sections]
            })
        elif path == "/api/trains":
            self._send_json([asdict(t) for t in STATE.trains])
        elif path == "/api/blocks":
            self._send_json([asdict(b) for b in STATE.blocks])
        elif path == "/api/assets":
            self._send_json([asdict(a) for a in STATE.assets])
        elif path == "/api/kpis":
            self._send_json(STATE.last_kpis)
        elif path == "/api/logs":
            self._send_json(STATE.event_logs)
        elif path.startswith("/api/memo/"):
            block_id = path.split("/")[-1]
            block = next((b for b in STATE.blocks if b.block_id == block_id), None)
            if not block:
                self._send_json({"error": "Block not found"}, 404)
            else:
                memo = self._generate_block_memo(block)
                self._send_json(memo)
        else:
            # Fallback to static files
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path == "/api/optimize":
            mode = payload.get("mode", "balanced")
            STATE.run_optimization(mode)
            self._send_json({
                "success": True,
                "mode": mode,
                "kpis": STATE.last_kpis,
                "blocks": [asdict(b) for b in STATE.blocks]
            })

        elif path == "/api/simulate-delay":
            train_no = payload.get("train_no")
            delay_min = int(payload.get("delay_min", 0))
            if not train_no:
                self._send_json({"error": "train_no is required"}, 400)
                return

            STATE.inject_delay(train_no, delay_min)
            self._send_json({
                "success": True,
                "train_no": train_no,
                "delay_min": delay_min,
                "kpis": STATE.last_kpis,
                "blocks": [asdict(b) for b in STATE.blocks]
            })

        elif path == "/api/request-block":
            try:
                new_block = MaintenanceBlock(
                    block_id=f"MB-{len(STATE.blocks) + 1:02d}",
                    department=Department(payload.get("department", Department.ENGINEERING)),
                    section_id=payload.get("section_id", "DN-ALJN-TDL"),
                    direction=TrackDirection(payload.get("direction", "DOWN")),
                    from_km=float(payload.get("from_km", 140.0)),
                    to_km=float(payload.get("to_km", 150.0)),
                    requested_start_min=int(payload.get("requested_start_min", 600)),
                    requested_duration_min=int(payload.get("requested_duration_min", 120)),
                    urgency_score=int(payload.get("urgency_score", 70)),
                    work_description=payload.get("work_description", "Manual Gang Inspection & Packing"),
                    machine_required=payload.get("machine_required", "Manual Squad"),
                    status=BlockStatus.REQUESTED
                )
                STATE.blocks.append(new_block)
                STATE.run_optimization(STATE.mode)
                self._send_json({
                    "success": True,
                    "new_block": asdict(new_block),
                    "kpis": STATE.last_kpis,
                    "blocks": [asdict(b) for b in STATE.blocks]
                })
            except Exception as e:
                self._send_json({"error": str(e)}, 400)

        elif path == "/api/reset":
            STATE.reset()
            self._send_json({"success": True, "message": "State reset to defaults"})
        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def _generate_block_memo(self, block: MaintenanceBlock) -> Dict:
        start_fmt = BlockOptimizer.format_min(block.granted_start_min or block.requested_start_min)
        duration = block.granted_duration_min or block.requested_duration_min
        end_fmt = BlockOptimizer.format_min((block.granted_start_min or block.requested_start_min) + duration)

        return {
            "memo_no": f"IR/NCR/PRYJ/BLK-2026/{block.block_id}",
            "date": "09-SEP-2026",
            "section_controller": "P. K. Sharma (Sr. DOM / T)",
            "division": "Prayagraj Division (North Central Railway)",
            "section": block.section_id,
            "track": block.direction.value,
            "km_range": f"KM {block.from_km:.1f} to {block.to_km:.1f}",
            "department": block.department.value,
            "machine": block.machine_required,
            "work": block.work_description,
            "sanctioned_window": f"{start_fmt} hrs to {end_fmt} hrs ({duration} Mins)",
            "block_type": "Shadow Block (Zero Punctuality Loss)" if block.shadow_block else "AI-Regulated Window",
            "safety_precaution": "Strict red aspect isolation, Axle counter clamp, OHE 25kV power cut permit required.",
            "digital_signature": "SHA256-IR-AI-7782B901C4FE9"
        }


def run_server():
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with socketserver.TCPServer(("", PORT), RailwayRequestHandler) as httpd:
        print(f"RailBlock AI Server running at http://localhost:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
