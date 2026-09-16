from database import init_db
from gui import launch_gui
from scheduler import start_scheduler


def main():
    init_db()
    scheduler = start_scheduler()

    try:
        launch_gui()
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
