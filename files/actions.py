"""Операции с файлами (с подтверждением для удаления)."""
from files.manager import FileManager


class FileActions:
    def __init__(self, workspace: str):
        self.fm = FileManager(workspace)

    def create_text_file(self, name: str, content: str = "") -> str:
        return self.fm.create_file(name, content)

    def delete_with_confirm(self, path: str, confirm_fn) -> bool:
        """confirm_fn(path) -> bool. Удаление только после подтверждения."""
        if not confirm_fn(path):
            return False
        return self.fm.delete(path)

    def rename_file(self, src: str, dst: str) -> str:
        return self.fm.rename(src, dst)

    def copy_file(self, src: str, dst: str) -> str:
        return self.fm.copy(src, dst)

    def read_file(self, path: str) -> str:
        return self.fm.read_text(path)
