from app import create_app
from app.services.scheduler_service import start_scheduler

app = create_app()

if __name__ == "__main__":
    start_scheduler()
    app.run(debug=True, use_reloader=False)
