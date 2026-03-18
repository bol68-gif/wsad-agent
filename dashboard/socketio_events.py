from dashboard.app import socketio
from datetime import datetime

@socketio.on("connect")
def handle_connect():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Client connected to logs")

@socketio.on("disconnect")
def handle_disconnect():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Client disconnected")

@socketio.on("ping_test")
def handle_ping(data):
    socketio.emit("pong_test", {"message": "Socket working!", "time": datetime.now().strftime("%H:%M:%S")})

def broadcast_log(agent_name, log_type, content):
    try:
        payload = {
            "agent_name": str(agent_name),
            "log_type":   str(log_type),
            "content":    str(content)[:2000],   # ← was 500, now 2000
            "timestamp":  datetime.now().strftime("%H:%M:%S")
        }
        socketio.emit("new_log", payload, namespace="/")
        print(f"[BROADCAST] {agent_name} | {log_type} | {str(content)[:80]}")
    except Exception as e:
        print(f"[BROADCAST ERROR] {e}")

def broadcast_agent_status(agent_name, status, current_task=""):
    try:
        socketio.emit("agent_status", {
            "agent_name":   str(agent_name),
            "status":       str(status),
            "current_task": str(current_task)[:200],
            "timestamp":    datetime.now().strftime("%H:%M:%S")
        }, namespace="/")
    except Exception as e:
        print(f"[STATUS ERROR] {e}")