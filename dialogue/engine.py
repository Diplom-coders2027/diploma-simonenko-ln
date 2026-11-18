"""Движок диалогов (rule-based, без ИИ)."""
import json
import os
import random
from typing import Optional


class DialogueEngine:
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self.phrases_path = os.path.join(assets_dir, "phrases.json")
        self.arch_path = os.path.join(assets_dir, "dialogue_arch.json")
        self._phrases = self._load_json(self.phrases_path, {})
        self._arch = self._load_json(self.arch_path, {})

    def _load_json(self, path: str, default):
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def reload(self):
        self._phrases = self._load_json(self.phrases_path, {})
        self._arch = self._load_json(self.arch_path, {})

    def categories(self) -> list:
        cats = set()
        if isinstance(self._phrases, dict):
            cats.update(self._phrases.keys())
        if isinstance(self._arch, dict):
            for k in self._arch.keys():
                cats.add(k)
        return sorted(cats)

    def pick(self, category: str, state=None) -> Optional[str]:
        """Выбирает реплику из категории. Поддерживает phrases.json и dialogue_arch.json."""
        user = getattr(state, "user_name", "Лев") if state else "Лев"
        mood = getattr(state, "mood", 70) if state else 70

        # 1. dialogue_arch: категория -> список объектов {text, ...} или строк
        arch_entry = None
        if isinstance(self._arch, dict):
            arch_entry = self._arch.get(category)
        if arch_entry:
            line = self._pick_from_entry(arch_entry, user, mood)
            if line:
                return line

        # 2. phrases.json: категория -> список строк
        ph_entry = None
        if isinstance(self._phrases, dict):
            ph_entry = self._phrases.get(category)
        if ph_entry:
            line = self._pick_from_entry(ph_entry, user, mood)
            if line:
                return line

        # 3. fallback: idle/greeting
        if category != "idle":
            return self.pick("idle", state)
        return None

    def _pick_from_entry(self, entry, user: str, mood: int) -> Optional[str]:
        # entry может быть: list[str], list[dict], dict с ключом "lines"/"phrases"
        candidates = None
        if isinstance(entry, list):
            candidates = entry
        elif isinstance(entry, dict):
            for key in ("lines", "phrases", "replies", "texts"):
                if key in entry and isinstance(entry[key], list):
                    candidates = entry[key]
                    break
            if candidates is None:
                # может быть dict: mood -> list
                # пробуем выбрать по настроению
                for key in ("happy", "neutral", "sad"):
                    if key in entry and isinstance(entry[key], list):
                        if mood >= 70 and key == "happy":
                            candidates = entry[key]; break
                        if mood <= 30 and key == "sad":
                            candidates = entry[key]; break
                        if key == "neutral":
                            candidates = entry[key]
        if not candidates:
            return None
        # candidates: list of str or dict
        texts = []
        for c in candidates:
            if isinstance(c, str):
                texts.append(c)
            elif isinstance(c, dict):
                t = c.get("text") or c.get("line") or c.get("reply")
                if t:
                    texts.append(t)
        if not texts:
            return None
        line = random.choice(texts)
        line = line.replace("{user}", user).replace("{name}", user)
        return line
