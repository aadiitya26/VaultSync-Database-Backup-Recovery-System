
import logging

from app import create_app
from app.services.scheduler_service import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = create_app()

if __name__ == "__main__":
    scheduler = start_scheduler()

    print("Scheduler running:", scheduler.running)

    for job in scheduler.get_jobs():
        print("Job ID:", job.id)
        print("Next run time:", job.next_run_time)

    app.run(debug=True, use_reloader=False)
