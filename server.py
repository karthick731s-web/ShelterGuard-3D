"""
3D LiDAR Shelter Inspection System — Flask API Server
Exposes API endpoints for the Disaster Response Command Center React Frontend.
"""

import os
import sys
import json
import time
import subprocess
import threading
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="reports")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
MAIN_SCRIPT = os.path.join(BASE_DIR, "ros2_ws", "src", "shelter_inspection", "main.py")

# Live execution state
execution_state = {
    "is_running": False,
    "progress_pct": 0,
    "current_phase": "Idle",
    "last_run_time": None,
    "logs": [],
}

def load_inspection_json():
    json_path = os.path.join(REPORTS_DIR, "inspection_summary.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading inspection_summary.json: {e}")
    
    # Fallback simulation payload if file does not exist yet
    return {
        "shelter_id": "SH-001",
        "robot_id": "TB3-01",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "severity": {
            "score": 86.8,
            "risk_level": "CRITICAL",
            "recommendation": "IMMINENT COLLAPSE RISK. Do NOT enter under any circumstances. Evacuate all personnel within 50 m radius immediately.",
            "confidence_overall": 0.82,
            "factor_breakdown": {
                "type_score": 60.0,
                "extent_penalty": 15.0,
                "count_penalty": 10.0,
                "confidence_adj": 1.8
            }
        },
        "damage_summary": {
            "total_count": 29,
            "total_area_m2": 18.4,
            "damage_types": ["Collapsed Section", "Leaning Wall", "Large Hole / Void"],
            "instances": [
                {
                    "type": "Collapsed Section",
                    "location_xyz": [2.0, 1.0, 1.1],
                    "extent_m": 1.3,
                    "confidence": 0.85,
                    "description": "North-west wall section collapse detected at (2.00, 1.00, 1.10). Wall fragmented and debris distributed over 1.3m."
                },
                {
                    "type": "Leaning Wall",
                    "location_xyz": [3.0, -0.79, 0.65],
                    "extent_m": 15.81,
                    "confidence": 1.0,
                    "description": "East Wall region shows tilt of 18.4° from vertical. Immediate structural assessment required."
                },
                {
                    "type": "Large Hole / Void",
                    "location_xyz": [2.56, 3.35, 0.0],
                    "extent_m": 14.52,
                    "confidence": 1.0,
                    "description": "Significant floor void detected in main shelter bay."
                }
            ]
        },
        "navigation_stats": {
            "distance_m": 31.1,
            "steps": 20,
            "battery_pct": 80.8,
            "scans_taken": 20
        },
        "scan_stats": {
            "total_scans": 8,
            "total_points": 202322,
            "valid_points": 199926
        }
    }


@app.route("/api/status", methods=["GET"])
def get_status():
    data = load_inspection_json()
    nav = data.get("navigation_stats", {})
    return jsonify({
        "robot_id": data.get("robot_id", "TB3-01"),
        "shelter_id": data.get("shelter_id", "SH-001"),
        "status": "Connected" if not execution_state["is_running"] else "Inspecting",
        "battery_pct": nav.get("battery_pct", 98),
        "distance_m": nav.get("distance_m", 31.1),
        "current_position": {"x": 6.75, "y": 5.25, "theta": 90.0},
        "navigation_progress": 100 if not execution_state["is_running"] else execution_state["progress_pct"],
        "is_running": execution_state["is_running"],
        "current_phase": execution_state["current_phase"],
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/api/inspection", methods=["GET"])
def get_inspection():
    return jsonify(load_inspection_json())


@app.route("/api/report", methods=["GET"])
def get_report():
    report_path = os.path.join(REPORTS_DIR, "inspection_report.txt")
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                return jsonify({"report": f.read(), "found": True})
        except Exception as e:
            return jsonify({"error": str(e), "found": False}), 500
    return jsonify({
        "report": "=== 3D LiDAR SHELTER INSPECTION REPORT ===\nStatus: Pending Execution\nPlease click 'Start Inspection' to run full diagnostic pipeline.",
        "found": False
    })


@app.route("/api/logs", methods=["GET"])
def get_logs():
    log_path = os.path.join(REPORTS_DIR, "inspection.log")
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return jsonify({"logs": [line.strip() for line in lines[-200:]]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Default initial logs if log file is empty
    return jsonify({"logs": [
        "2026-07-25 14:00:00 | INFO | System initialized.",
        "2026-07-25 14:00:01 | INFO | Ready to start 3D LiDAR inspection."
    ]})


@app.route("/api/images/<filename>", methods=["GET"])
def get_image(filename):
    allowed = ["point_cloud.png", "environment_map.png", "damage_heatmap.png"]
    if filename not in allowed:
        return jsonify({"error": "Invalid image request"}), 400
    if os.path.exists(os.path.join(REPORTS_DIR, filename)):
        return send_from_directory(REPORTS_DIR, filename)
    else:
        return jsonify({"error": "File not found"}), 404


def run_pipeline_worker():
    execution_state["is_running"] = True
    execution_state["progress_pct"] = 10
    execution_state["current_phase"] = "Initializing Robot..."

    cmd = [sys.executable, MAIN_SCRIPT, "--no-plot"]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.path.dirname(MAIN_SCRIPT),
            text=True,
            bufsize=1
        )
        
        for line in iter(proc.stdout.readline, ''):
            line_str = line.strip()
            if line_str:
                execution_state["logs"].append(line_str)
                if "Initialising Robot" in line_str:
                    execution_state["progress_pct"] = 15
                    execution_state["current_phase"] = "Robot Initialization"
                elif "Autonomous Navigation" in line_str:
                    execution_state["progress_pct"] = 30
                    execution_state["current_phase"] = "Autonomous Navigation"
                elif "LiDAR Scans" in line_str:
                    execution_state["progress_pct"] = 45
                    execution_state["current_phase"] = "3D LiDAR Scanning"
                elif "Point Cloud" in line_str:
                    execution_state["progress_pct"] = 60
                    execution_state["current_phase"] = "Point Cloud Generation"
                elif "Environment Map" in line_str:
                    execution_state["progress_pct"] = 75
                    execution_state["current_phase"] = "3D Environment Mapping"
                elif "Damage" in line_str:
                    execution_state["progress_pct"] = 85
                    execution_state["current_phase"] = "Structural Damage Detection"
                elif "Severity" in line_str:
                    execution_state["progress_pct"] = 95
                    execution_state["current_phase"] = "Severity Classification"
                elif "Report" in line_str:
                    execution_state["progress_pct"] = 100
                    execution_state["current_phase"] = "Report Generation Complete"

        proc.wait()
    except Exception as e:
        print(f"Error running pipeline: {e}")
    finally:
        execution_state["is_running"] = False
        execution_state["progress_pct"] = 100
        execution_state["current_phase"] = "Completed"
        execution_state["last_run_time"] = time.strftime("%Y-%m-%d %H:%M:%S")


@app.route("/api/run-inspection", methods=["POST"])
def trigger_inspection():
    if execution_state["is_running"]:
        return jsonify({"message": "Inspection already in progress", "status": "running"}), 400

    thread = threading.Thread(target=run_pipeline_worker)
    thread.daemon = True
    thread.start()

    return jsonify({
        "message": "Inspection pipeline started successfully",
        "status": "started"
    })


if __name__ == "__main__":
    print("==========================================================")
    print("3D LiDAR Shelter Inspection API Server running on port 5000")
    print("==========================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)
