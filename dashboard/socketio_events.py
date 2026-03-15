from dashboard.app import socketio 
from datetime import datetime 
 
@socketio.on("connect") 
def handle_connect(): 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Browser connected to Socket.IO") 
 
@socketio.on("disconnect") 
def handle_disconnect(): 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Browser disconnected") 
 
def broadcast_log(agent_name, log_type, content): 
    try: 
        payload = { 
            "agent_name": str(agent_name), 
            "log_type":   str(log_type), 
            "content":    str(content)[:500], 
            "timestamp":  datetime.now().strftime("%H:%M:%S") 
        } 
        socketio.emit("new_log", payload, namespace="/") 
        print(f"[EMIT ✅] {agent_name} | {log_type} | {str(content)[:60]}") 
    except Exception as e: 
        print(f"[EMIT ❌] {e}") 
 
def broadcast_agent_status(agent_name, status, current_task=""): 
    try: 
        socketio.emit("agent_status", { 
            "agent_name":   str(agent_name), 
            "status":       str(status), 
            "current_task": str(current_task)[:100], 
            "timestamp":    datetime.now().strftime("%H:%M:%S") 
        }, namespace="/") 
    except Exception as e: 
        print(f"[STATUS ERROR] {e}") 
