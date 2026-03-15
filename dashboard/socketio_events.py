from dashboard.app import socketio
from flask_socketio import emit

@socketio.on("connect")
def handle_connect():
    print("Dashboard client connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("Dashboard client disconnected")

def broadcast_log(agent_name, log_type, content):
    """
    Broadcasts a log message to all connected clients.
    agent_name: str (e.g., 'Director', 'Analyst')
    log_type: str ('info', 'warning', 'error', 'success')
    content: str (The log message)
    """
    emit('new_log', {
        'agent_name': agent_name,
        'log_type': log_type,
        'content': content,
        'timestamp': None # Can be filled by client or passed
    }, namespace='/', broadcast=True)

def broadcast_agent_status(agent_name, status, current_task):
    """
    Updates the status of an agent for all connected clients.
    agent_name: str
    status: str ('idle', 'working', 'error')
    current_task: str
    """
    emit('agent_status', {
        'agent_name': agent_name,
        'status': status,
        'current_task': current_task
    }, namespace='/', broadcast=True)
