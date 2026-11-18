"""Менеджер файлов (полный доступ, кроме системных папок)."""
import os
import shutil
import hashlib
import mimetypes
import platform
from datetime import datetime


def _system_paths() -> list:
    paths = []
    system = platform.system()
    if system == "Windows":
        for env in ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramData"):
            v = os.environ.get(env)
            if v:
                paths.append(v)
        for p in ("C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)",
                  "C:\\ProgramData", "C:\\$Recycle.Bin"):
            paths.append(p)
    else:
        for p in ("/etc", "/usr", "/bin", "/sbin", "/lib", "/lib64", "/boot",
                  "/proc", "/sys", "/dev", "/root/.ssh"):
            paths.append(p)
    seen = set()
    result = []
    for p in paths:
        np = os.path.normpath(p).lower()
        if np not in seen:
            seen.add(np)
            result.append(np)
    return result


SYSTEM_PATHS = _system_paths()


class FileManager:
    def __init__(self, workspace: str = None):
        if workspace:
            self.workspace = os.path.abspath(workspace)
            os.makedirs(self.workspace, exist_ok=True)
        else:
            self.workspace = os.path.abspath(os.getcwd())
        self.home = os.path.expanduser("~")

    def _safe(self, path: str) -> str:
        if os.path.isabs(path):
            full = os.path.abspath(path)
        else:
            full = os.path.abspath(os.path.join(self.workspace, path))
        full_norm = os.path.normpath(full)
        low = full_norm.lower()
        for sp in SYSTEM_PATHS:
            if low == sp or low.startswith(sp + os.sep.lower()):
                raise ValueError(f"Доступ к системной папке запрещён: {full}")
        return full_norm

    def list_dir(self, subpath: str = "") -> list:
        full = self._safe(subpath) if subpath else self.workspace
        if not os.path.isdir(full):
            return []
        items = []
        try:
            for name in sorted(os.listdir(full)):
                p = os.path.join(full, name)
                items.append({
                    "name": name,
                    "path": p,
                    "is_dir": os.path.isdir(p),
                    "size": os.path.getsize(p) if os.path.isfile(p) else 0,
                })
        except PermissionError:
            pass
        return items

    def metadata(self, path: str) -> dict:
        full = self._safe(path)
        if not os.path.exists(full):
            raise FileNotFoundError(path)
        st = os.stat(full)
        info = {
            "имя": os.path.basename(full) or full,
            "путь": full,
            "тип": "папка" if os.path.isdir(full) else (mimetypes.guess_type(full)[0] or "неизвестно"),
            "размер (байт)": st.st_size,
            "создан": datetime.fromtimestamp(st.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
            "изменён": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        }
        if os.path.isfile(full):
            if st.st_size < 10 * 1024 * 1024:
                h = hashlib.sha256()
                with open(full, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        h.update(chunk)
                info["sha256"] = h.hexdigest()[:16] + "…"
            if mimetypes.guess_type(full)[0] and mimetypes.guess_type(full)[0].startswith("text"):
                try:
                    with open(full, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()[:5]
                    info["превью"] = "".join(lines)[:200]
                except Exception:
                    pass
        return info

    def create_file(self, path: str, content: str = "") -> str:
        full = self._safe(path)
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return full

    def create_dir(self, path: str) -> str:
        full = self._safe(path)
        os.makedirs(full, exist_ok=True)
        return full

    def delete(self, path: str) -> bool:
        full = self._safe(path)
        if not os.path.exists(full):
            return False
        if os.path.isdir(full) and not os.path.islink(full):
            shutil.rmtree(full)
        else:
            os.remove(full)
        return True

    def rename(self, src: str, dst: str) -> str:
        s = self._safe(src)
        d = self._safe(dst)
        os.makedirs(os.path.dirname(d) or ".", exist_ok=True)
        os.rename(s, d)
        return d

    def copy(self, src: str, dst: str) -> str:
        s = self._safe(src)
        d = self._safe(dst)
        os.makedirs(os.path.dirname(d) or ".", exist_ok=True)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
        return d

    def read_text(self, path: str, max_bytes: int = 100000) -> str:
        full = self._safe(path)
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_bytes)

    def write_text(self, path: str, content: str) -> str:
        full = self._safe(path)
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return full
