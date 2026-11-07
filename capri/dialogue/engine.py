# dialogue/engine.py — правило-ориентированный движок диалогов
import json
import os
import random

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class DialogueEngine:
    def __init__(self, phrases_path=None):
        if phrases_path is None:
            phrases_path = os.path.join(ASSETS_DIR, "phrases.json")
        self.phrases = {}
        if os.path.exists(phrases_path):
            with open(phrases_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.phrases = data.get("phrases", {})

    def get_phrases(self, event_type: str) -> list:
        entry = self.phrases.get(event_type, {})
        return entry.get("templates", [])

    def random_phrase(self, event_type: str) -> str | None:
        templates = self.get_phrases(event_type)
        if not templates:
            return None
        return random.choice(templates)

    def all_event_types(self) -> list:
        return list(self.phrases.keys())