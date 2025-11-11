import os
import time
import uuid
from threading import Thread, Event, Lock
from flask import Flask, jsonify, request, render_template, send_from_directory

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(
    __name__,
    static_folder=None,
    template_folder=TEMPLATE_DIR
)

# ------------------------------------------------------------
# Data Structures (Per-lane Queue)
# ------------------------------------------------------------
lanes = ["North", "East", "South", "West"]
traffic_queues = {lane: [] for lane in lanes}
queue_lock = Lock()

# Current signal state
current_signal = {"active": None, "previous": None}

# Control flags
auto_mode = Event()
stop_event = Event()

# Default signal time (seconds)
signal_time = 3


# ------------------------------------------------------------
# Helper function
# ------------------------------------------------------------
def flatten_queues():
    """Combine all queues into a single list for frontend rendering."""
    all_items = []
    for lane, q in traffic_queues.items():
        all_items.extend(q)
    return all_items


# ------------------------------------------------------------
# Auto signal control thread (with yellow transition)
# ------------------------------------------------------------
def auto_signal_cycle():
    """Cycle through signals automatically and dequeue vehicles."""
    print("[AUTO MODE] Started.")
    while not stop_event.is_set():
        for sig in lanes:
            if stop_event.is_set():
                break

            # Yellow transition from previous
            with queue_lock:
                current_signal["previous"] = current_signal["active"]
                current_signal["active"] = None
            time.sleep(1)  # Yellow delay

            # Green for current lane
            with queue_lock:
                current_signal["previous"] = None
                current_signal["active"] = sig
                print(f"[SIGNAL] {sig} lane is GREEN.")

            # Dequeue one vehicle per second during green signal
            for _ in range(signal_time):
                if stop_event.is_set():
                    break
                with queue_lock:
                    if traffic_queues[sig]:
                        vehicle = traffic_queues[sig].pop(0)
                        print(f"[AUTO] {vehicle} passed from {sig} lane.")
                time.sleep(1)

        time.sleep(0.5)

    print("[AUTO MODE] Stopped.")


auto_thread = None


# ------------------------------------------------------------
# Serve static files safely (CSS/JS)
# ------------------------------------------------------------
@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(STATIC_DIR, filename)


# ------------------------------------------------------------
# Frontend route
# ------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ------------------------------------------------------------
# API: Enqueue (fixed per selected lane)
# ------------------------------------------------------------
@app.route("/api/enqueue", methods=["POST"])
def api_enqueue():
    data = request.get_json()
    vehicle = data.get("vehicle", f"Vehicle-{uuid.uuid4().hex[:4]}")
    lane = data.get("lane", "North")  # use selected lane

    with queue_lock:
        if lane not in traffic_queues:
            traffic_queues[lane] = []
        traffic_queues[lane].append(vehicle)

    print(f"[ENQUEUE] {vehicle} added to {lane} lane.")
    return jsonify({"message": f"{vehicle} added to {lane} lane.", "queue": flatten_queues()})


# ------------------------------------------------------------
# API: Manual Dequeue
# ------------------------------------------------------------
@app.route("/api/dequeue", methods=["POST"])
def api_dequeue():
    with queue_lock:
        lane = current_signal["active"]
        if lane and traffic_queues[lane]:
            vehicle = traffic_queues[lane].pop(0)
            msg = f"{vehicle} passed from {lane} lane."
            print(f"[DEQUEUE] {msg}")
        else:
            msg = "No vehicle to dequeue."
            print("[DEQUEUE] Nothing to remove.")
    return jsonify({"message": msg, "queue": flatten_queues()})


# ------------------------------------------------------------
# API: Reset system
# ------------------------------------------------------------
@app.route("/api/reset", methods=["POST"])
def api_reset():
    with queue_lock:
        for lane in lanes:
            traffic_queues[lane].clear()
        current_signal["active"] = None
        current_signal["previous"] = None
    stop_event.set()
    auto_mode.clear()
    print("[RESET] System reset complete.")
    return jsonify({"message": "System reset complete.", "queue": []})


# ------------------------------------------------------------
# API: Get current status
# ------------------------------------------------------------
@app.route("/api/status", methods=["GET"])
def api_status():
    with queue_lock:
        return jsonify({
            "queue": flatten_queues(),
            "current_signal": current_signal["active"],
            "prev_signal": current_signal["previous"]
        })


# ------------------------------------------------------------
# API: Manually change signal
# ------------------------------------------------------------
@app.route("/api/change_signal", methods=["POST"])
def api_change_signal():
    data = request.get_json()
    new_signal = data.get("signal")
    with queue_lock:
        if new_signal in lanes:
            current_signal["previous"] = current_signal["active"]
            current_signal["active"] = new_signal
            msg = f"Signal changed to {new_signal}."
            print(f"[SIGNAL] {msg}")
        else:
            msg = "Invalid signal name."
    return jsonify({"message": msg})


# ------------------------------------------------------------
# API: Start auto mode
# ------------------------------------------------------------
@app.route("/api/start_auto", methods=["POST"])
def api_start_auto():
    global auto_thread, signal_time

    data = request.get_json()
    user_time = data.get("signal_time")
    if user_time:
        signal_time = int(user_time)

    if not auto_mode.is_set():
        auto_mode.set()
        stop_event.clear()
        auto_thread = Thread(target=auto_signal_cycle, daemon=True)
        auto_thread.start()
        msg = f"Auto mode started (interval: {signal_time}s per lane)."
        print(f"[AUTO] {msg}")
        return jsonify({"message": msg})

    return jsonify({"message": "Auto mode already running."})


# ------------------------------------------------------------
# API: Stop auto mode
# ------------------------------------------------------------
@app.route("/api/stop_auto", methods=["POST"])
def api_stop_auto():
    if auto_mode.is_set():
        auto_mode.clear()
        stop_event.set()
        print("[AUTO] Auto mode stopped by user.")
        return jsonify({"message": "Auto mode stopped."})
    return jsonify({"message": "Auto mode not active."})


# ------------------------------------------------------------
# API: Explain (for documentation)
# ------------------------------------------------------------
@app.route("/api/explain", methods=["GET"])
def api_explain():
    return jsonify({
        "project": "Traffic Queue Management System",
        "description": (
            "Simulates traffic queue management using queue data structures. "
            "Each lane has its own queue. Auto mode cycles signals (Red → Yellow → Green) "
            "and dequeues vehicles from the active lane with smooth transitions."
        )
    })


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    print("STATIC DIR:", STATIC_DIR)
    print("TEMPLATE DIR:", TEMPLATE_DIR)
    print("FILES IN STATIC:", os.listdir(STATIC_DIR))
    app.run(debug=True)
