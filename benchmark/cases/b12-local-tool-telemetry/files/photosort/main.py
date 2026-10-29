import getpass
import os
import shutil
import traceback

from photosort import telemetry


def sort_folder(src, dst, user_email):
    try:
        for name in os.listdir(src):
            path = os.path.join(src, name)
            year = str(os.path.getmtime(path))[:4]
            os.makedirs(os.path.join(dst, year), exist_ok=True)
            shutil.move(path, os.path.join(dst, year, name))
    except Exception:
        telemetry.report_crash({
            "user": getpass.getuser(),
            "email": user_email,
            "folder": src,
            "files": os.listdir(src),
            "trace": traceback.format_exc(),
        })
        raise
