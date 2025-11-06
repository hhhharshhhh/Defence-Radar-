import socket
import threading
import time
import random
import json

HOST = "192.168.1.7"
PORT = 5050

tracks = {}   
tracks_lock = threading.Lock()
next_track_id = 1

def simulate_environment():
    """
    Periodically mutates tracks: new targets appear, some move, some disappear.
    Runs in background thread.
    """
    global next_track_id
    while True:
        time.sleep(2)  # environment update interval

        with tracks_lock:
            # Small chance to spawn a new object
            if random.random() < 0.4 and len(tracks) < 12:
                tid = next_track_id
                next_track_id += 1
                tracks[tid] = {
                    "id": tid,
                    "range_m": random.uniform(500, 20000),  # meters
                    "velocity_mps": random.uniform(-200, 200),  # negative = closing
                    "angle_deg": random.uniform(0, 360),
                    "last_seen": time.time()
                }

            # Update existing tracks
            remove_ids = []
            for tid, t in tracks.items():
                # small random movement
                t["range_m"] += t["velocity_mps"] * random.uniform(0.5, 2.0)
                t["angle_deg"] = (t["angle_deg"] + random.uniform(-3, 3)) % 360
                t["velocity_mps"] += random.uniform(-2, 2)
                t["velocity_mps"] = max(min(t["velocity_mps"], 800), -800)
                t["last_seen"] = time.time()

                # disappear if out of range or random chance
                if t["range_m"] < 50 or t["range_m"] > 100000 or random.random() < 0.03:
                    remove_ids.append(tid)

            for rid in remove_ids:
                del tracks[rid]


def format_tracks_short():
    """
    Returns compact textual representation of current tracks.
    """
    with tracks_lock:
        lst = []
        for t in sorted(tracks.values(), key=lambda x: x["id"]):
            lst.append({
                "id": t["id"],
                "range_m": round(t["range_m"], 1),
                "vel_mps": round(t["velocity_mps"], 2),
                "angle_deg": round(t["angle_deg"], 1)
            })
    return json.dumps({"tracks": lst}, indent=2)


def handle_command(cmd_text: str) -> str:
    """
    Core command handling. Returns a human-readable or JSON string.
    """
    # Emulate processing time & compute simple throughput stats
    start = time.time()
    cmd = cmd_text.strip().lower()

    # HELP
    if cmd in ("help", "?"):
        return (
            "Commands:\n"
            " - scan         : perform a radar sweep and return detected objects\n"
            " - report       : current tracked objects\n"
            " - analyze      : simulated throughput/latency metrics\n"
            " - track <id>   : detailed info for target id\n"
            " - clear        : clear all tracks\n"
            " - help         : this message\n"
        )

    if cmd == "scan":
        # Simulate scanning cost proportional to number of objects
        with tracks_lock:
            # slight chance to generate instant contacts during scan
            for _ in range(random.randint(0, 3)):
                if random.random() < 0.5:
                    tid = max(list(tracks.keys()) or [0]) + 1
                    tracks[tid] = {
                        "id": tid,
                        "range_m": random.uniform(300, 15000),
                        "velocity_mps": random.uniform(-150, 150),
                        "angle_deg": random.uniform(0, 360),
                        "last_seen": time.time()
                    }
            # copy snapshot
            snapshot = [dict(t) for t in tracks.values()]

        # simulate processing delay
        processing = 0.05 + 0.001 * len(snapshot) + random.uniform(0, 0.03)
        time.sleep(processing)

        # Build response
        data = {
            "type": "scan",
            "timestamp": time.time(),
            "count": len(snapshot),
            "targets": [
                {
                    "id": t["id"],
                    "range_m": round(t["range_m"], 1),
                    "vel_mps": round(t["velocity_mps"], 2),
                    "angle_deg": round(t["angle_deg"], 1)
                } for t in snapshot
            ]
        }
        duration = time.time() - start
        data["processing_s"] = round(duration, 4)
        data["throughput_est_ops_per_s"] = round((len(snapshot) + 1) / (duration + 1e-6), 2)
        return json.dumps(data, indent=2)

    if cmd == "report":
        # return tracked objects in short JSON
        return format_tracks_short()

    if cmd.startswith("track "):
        try:
            tid = int(cmd.split()[1])
        except:
            return "Usage: track <id> (integer)"
        with tracks_lock:
            t = tracks.get(tid)
            if not t:
                return f"Target {tid} not found."
            # Add some computed fields
            time_since = round(time.time() - t["last_seen"], 2)
            doppler = round(t["velocity_mps"], 2)
            data = {
                "id": t["id"],
                "range_m": round(t["range_m"], 2),
                "velocity_mps": round(t["velocity_mps"], 3),
                "angle_deg": round(t["angle_deg"], 2),
                "last_seen_sec": time_since,
                "doppler_approx": doppler
            }
        return json.dumps(data, indent=2)

    if cmd == "clear":
        with tracks_lock:
            tracks.clear()
        return "All tracks cleared."

    if cmd == "analyze":
        # Simulate a stress test and compute throughput and avg latency
        num_ops = random.randint(50, 300)
        latencies = []
        for _ in range(num_ops):
            lat = random.uniform(0.001, 0.02)
            latencies.append(lat)
        avg_latency = sum(latencies) / len(latencies)
        throughput = round(1.0 / avg_latency * random.uniform(0.6, 1.0), 2)  # ops/sec
        return json.dumps({
            "type": "analysis",
            "ops_simulated": num_ops,
            "avg_latency_s": round(avg_latency, 6),
            "throughput_ops_per_s": throughput,
            "timestamp": time.time()
        }, indent=2)

    return "Unknown command. Type 'help' to see available commands."


def client_thread(conn, addr):
    """
    Handle one TCP client connection: read command, reply, close.
    """
    try:
        data = conn.recv(4096)
        if not data:
            return
        cmd_text = data.decode("utf-8").strip()
        print(f"[REQ] {addr} -> {cmd_text}")
        # Process
        reply = handle_command(cmd_text)
        # Ensure reply is bytes
        conn.sendall(reply.encode("utf-8"))
        print(f"[RESP] {addr} <- reply (len {len(reply)})")
    except Exception as e:
        try:
            conn.sendall(f"ERROR: {str(e)}".encode("utf-8"))
        except:
            pass
        print(f"[ERR] handling {addr}: {e}")
    finally:
        conn.close()


def start_server():
    # start environment simulator
    sim_thread = threading.Thread(target=simulate_environment, daemon=True)
    sim_thread.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(8)
        print(f"💬 Radar Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            thr = threading.Thread(target=client_thread, args=(conn, addr), daemon=True)
            thr.start()

if __name__ == "__main__":
    start_server()
