from dashboard.app import create_app, socketio 
 
app = create_app() 
 
from distribution.telegram_bot import start_bot 
from scheduler import setup_scheduler 

# Start services on import (required for Gunicorn)
print("\n" + "="*50) 
print("RF AGENT STARTING") 
print("="*50) 
print("Starting Telegram bot...") 
start_bot() 
print("Starting scheduler...") 
setup_scheduler() 
print("Dashboard: http://localhost:5000") 
print("="*50 + "\n") 

if __name__ == "__main__": 
    port = int(os.environ.get("PORT", 5000))
    socketio.run( 
        app, 
        host         = "0.0.0.0", 
        port         = port, 
        debug        = False, 
        use_reloader = False, 
        log_output   = True 
    ) 
