import sys

from app.control_center import run as run_control_center
from app.ui import run as run_dashboard


if __name__ == "__main__":
    if "--dashboard" in sys.argv:
        run_dashboard()
    else:
        run_control_center()
