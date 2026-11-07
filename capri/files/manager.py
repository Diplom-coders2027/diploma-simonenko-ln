# files/manager.py — работа с файлами в рабочей директории
import os
import shutil

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def work_dir() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wd = os.path.join(base, "capri_workspace")
    os.makedirs(wd, exist_ok=True)
    return wd


def list_files(subdir: str = "") -> list:
    target = os.path.join(work_dir(), subdir) if subdir else work_dir()
    os.makedirs(target, exist_ok=True)
    result = []
    for name in os.listdir(target):
        path = os.path.join(target, name)
        if os.path.isdir(path):
            result.append(f"[dir] {name}")
        else:
            result.append(name)
    return result


def read_file(path: str) -> str:
    full = os.path.join(work_dir(), path)
    if not os.path.abspath(full).startswith(os.path.abspath(work_dir())):
        raise PermissionError("Access denied: path outside workspace")
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str):
    full = os.path.join(work_dir(), path)
    if not os.path.abspath(full).startswith(os.path.abspath(work_dir())):
        raise PermissionError("Access denied: path outside workspace")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def delete_file(path: str):
    full = os.path.join(work_dir(), path)
    if not os.path.abspath(full).startswith(os.path.abspath(work_dir())):
        raise PermissionError("Access denied: path outside workspace")
    if os.path.isfile(full):
        os.remove(full)
    elif os.path.isdir(full):
        shutil.rmtree(full)