from dashboard.app import socketio

@socketio.on("connect")
def handle_connect():
    print("Dashboard client connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("Dashboard client disconnected")
