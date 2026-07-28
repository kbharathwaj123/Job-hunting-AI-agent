"""
Self-Learning Memory Module for AI Job Agent.

Remembers successful form field selectors, question-answer patterns,
and site-specific application flows. Saves learned strategies to data/learned_patterns.json
so future runs execute instantly without re-evaluating layout.
"""

import os
import json
from pathlib import Path

MEMORY_FILE = Path(__file__).parent.parent / "data" / "learned_patterns.json"

class MemoryStore:
    def __init__(self, memory_file: Path = MEMORY_FILE):
        self.memory_file = memory_file
        self.data = {
            "form_patterns": {},    # label_key -> answer/selector mapping
            "domain_flows": {},     # domain -> working form container/submit selectors
            "learned_questions": {} # screening question text -> verified answer
        }
        self.load()

    def load(self):
        """Loads learned patterns from JSON storage."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    self.data.update(content)
            except Exception as e:
                print(f"[MEMORY WARNING] Could not load memory file: {e}")

    def save(self):
        """Saves memory data to JSON storage."""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MEMORY WARNING] Could not save memory file: {e}")

    def get_question_answer(self, question: str):
        """Checks if we have a learned answer for a screening question."""
        key = question.lower().strip()
        return self.data["learned_questions"].get(key)

    def save_question_answer(self, question: str, answer: str):
        """Saves a verified question-answer pair into memory."""
        if not question or not answer:
            return
        key = question.lower().strip()
        if self.data["learned_questions"].get(key) != answer:
            self.data["learned_questions"][key] = str(answer)
            self.save()
            print(f"  [LEARNED MEMORY 🧠] Saved question pattern: '{key[:40]}' -> '{answer}'")

    def get_domain_flow(self, domain: str):
        """Gets learned modal/form selectors for a specific domain."""
        return self.data["domain_flows"].get(domain.lower())

    def save_domain_flow(self, domain: str, flow_info: dict):
        """Saves domain-specific form flow details."""
        dom = domain.lower()
        if dom not in self.data["domain_flows"]:
            self.data["domain_flows"][dom] = {}
        self.data["domain_flows"][dom].update(flow_info)
        self.save()
        print(f"  [LEARNED MEMORY 🧠] Saved domain workflow for '{dom}'")

# Global singleton memory instance
memory = MemoryStore()
