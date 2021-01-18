import psutil
import re
import logging

logging.basicConfig(level=logging.DEBUG)

def close_all_app(app_name: str):
    for p in psutil.process_iter():
        if re.match(app_name, p.name()):
            p.kill()

def is_any_running(app_name: str) -> bool:
    for p in psutil.process_iter():
        if re.match(app_name, p.name()):
            return True
    return False