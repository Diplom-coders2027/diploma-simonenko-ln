"""Сбор метаданных активного окна (кроссплатформенно)."""
import os
import sys
import subprocess
import platform


def get_active_window_metadata() -> dict:
    meta = {}
    system = platform.system()
    try:
        if system == "Windows":
            import win32gui
            import win32process
            import win32con
            import psutil
            hwnd = win32gui.GetForegroundWindow()
            # Пропускаем окна самого Капри (всегда поверх)
            def is_capri(h):
                try:
                    return "capri" in win32gui.GetWindowText(h).lower()
                except Exception:
                    return False
            while hwnd and is_capri(hwnd):
                hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDPREV)
            # Пропускаем невидимые окна
            while hwnd and not win32gui.IsWindowVisible(hwnd):
                hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDPREV)
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(pid)
                name = proc.name()
                exe = proc.exe()
                cpu = proc.cpu_percent(interval=0.1)
                mem = proc.memory_info().rss // 1024 // 1024
            except Exception:
                name, exe, cpu, mem = "?", "?", 0, 0
            meta["Заголовок"] = title or "(без названия)"
            meta["PID"] = pid
            meta["Процесс"] = name
            meta["Exe"] = exe
            meta["CPU%"] = cpu
            meta["RAM (MB)"] = mem
        elif system == "Linux":
            # xdotool
            try:
                wid = subprocess.check_output(["xdotool", "getactivewindow"], text=True).strip()
                title = subprocess.check_output(["xdotool", "getwindowname", wid], text=True).strip()
            except Exception:
                wid, title = "", "(xdotool не установлен)"
            # pid через xprop
            pid = ""
            try:
                out = subprocess.check_output(["xprop", "-id", wid, "_NET_WM_PID"], text=True)
                pid = out.split()[-1]
            except Exception:
                pid = ""
            meta["Заголовок"] = title
            meta["Window ID"] = wid
            if pid:
                meta["PID"] = pid
                try:
                    import psutil
                    proc = psutil.Process(int(pid))
                    meta["Процесс"] = proc.name()
                    meta["Exe"] = proc.exe()
                    meta["RAM (MB)"] = proc.memory_info().rss // 1024 // 1024
                except Exception:
                    pass
        elif system == "Darwin":
            meta["Система"] = "macOS (не реализовано)"
        else:
            meta["Система"] = system
    except Exception as e:
        meta["Ошибка"] = str(e)
    # Общие: время
    import datetime
    meta["Время"] = datetime.datetime.now().strftime("%H:%M:%S")
    return meta


def get_process_list(limit: int = 20) -> list:
    """Список запущенных процессов (имя, pid, ram)."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                info = p.info
                ram = info["memory_info"].rss // 1024 // 1024 if info.get("memory_info") else 0
                procs.append({"pid": info["pid"], "name": info["name"], "ram_mb": ram})
            except Exception:
                continue
        procs.sort(key=lambda x: x["ram_mb"], reverse=True)
        return procs[:limit]
    except Exception:
        return []


def get_system_info() -> dict:
    """Базовая информация о системе."""
    info = {}
    try:
        import psutil
        info["CPU%"] = psutil.cpu_percent(interval=0.2)
        vm = psutil.virtual_memory()
        info["RAM всего (MB)"] = vm.total // 1024 // 1024
        info["RAM свободно (MB)"] = vm.available // 1024 // 1024
        info["RAM использовано (%)"] = vm.percent
        info["Диски"] = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                info["Диски"].append(f"{part.device}: {usage.percent}% ({usage.free // 1024 // 1024} MB свободно)")
            except Exception:
                pass
    except Exception as e:
        info["Ошибка"] = str(e)
    return info
