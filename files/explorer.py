"""Обзор файловой системы (только для чтения, scoped)."""
import os
from files.manager import FileManager


class FileExplorer:
    def __init__(self, workspace: str):
        self.fm = FileManager(workspace)

    def tree(self, subpath: str = "", depth: int = 3) -> str:
        """Текстовое дерево файлов."""
        lines = []

        def walk(rel, level):
            if level > depth:
                return
            try:
                items = self.fm.list_dir(rel)
            except Exception:
                return
            for item in items:
                indent = "  " * level
                icon = "📁" if item["is_dir"] else "📄"
                lines.append(f"{indent}{icon} {item['name']}")
                if item["is_dir"]:
                    walk(item["path"], level + 1)

        walk(subpath, 0)
        return "\n".join(lines) if lines else "(пусто)"

    def search(self, query: str, subpath: str = "") -> list:
        """Поиск файлов по имени."""
        result = []
        try:
            items = self.fm.list_dir(subpath)
        except Exception:
            return result
        for item in items:
            if query.lower() in item["name"].lower():
                result.append(item)
            if item["is_dir"]:
                result.extend(self.search(query, item["path"]))
        return result
