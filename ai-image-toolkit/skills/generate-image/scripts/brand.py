#!/usr/bin/env python3
"""Brand configuration loader for image generation."""

import json
import sys
from pathlib import Path

DEFAULT_FILENAME = ".image-brand.json"


class BrandConfig:
    """Loads and applies brand configuration from a JSON file."""

    def __init__(self, config_path=None):
        self.data = {}
        path = self._resolve_path(config_path)
        if path:
            try:
                self.data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: could not load brand config from {path}: {e}", file=sys.stderr)

    def _resolve_path(self, config_path=None):
        if config_path:
            p = Path(config_path)
            if p.is_file():
                return p
            return None
        candidates = [Path.cwd() / DEFAULT_FILENAME, Path(__file__).parent.parent.parent.parent / DEFAULT_FILENAME]
        for p in candidates:
            if p.is_file():
                return p
        return None

    @property
    def background(self):
        return self.data.get("background", "")

    @property
    def accent(self):
        return self.data.get("accent", "")

    @property
    def text_primary(self):
        return self.data.get("text_primary", "")

    @property
    def text_secondary(self):
        return self.data.get("text_secondary", "")

    @property
    def font_family(self):
        return self.data.get("font_family", "")

    @property
    def font_weight_heading(self):
        return self.data.get("font_weight_heading", "")

    @property
    def font_weight_body(self):
        return self.data.get("font_weight_body", "")

    @property
    def canvas_size(self):
        return self.data.get("canvas_size", "")

    @property
    def style_notes(self):
        return self.data.get("style_notes", "")

    def canvas_dimensions(self):
        """Parse canvas_size into (width, height) tuple, or None."""
        size = self.canvas_size
        if not size:
            return None
        try:
            parts = size.lower().split("x")
            if len(parts) == 2:
                return (int(parts[0]), int(parts[1]))
        except (ValueError, AttributeError):
            pass
        return None

    def apply_to_prompt(self, prompt):
        """Append brand style context to a prompt."""
        if not self.data:
            return prompt
        parts = [prompt]
        if self.style_notes:
            parts.append(f"Style: {self.style_notes}")
        color_parts = []
        if self.background:
            color_parts.append(f"background {self.background}")
        if self.accent:
            color_parts.append(f"accent {self.accent}")
        if self.text_primary:
            color_parts.append(f"primary text {self.text_primary}")
        if self.text_secondary:
            color_parts.append(f"secondary text {self.text_secondary}")
        if color_parts:
            parts.append("Colors: " + ", ".join(color_parts))
        font_parts = []
        if self.font_family:
            font_parts.append(self.font_family)
        if self.font_weight_heading:
            font_parts.append(f"headings {self.font_weight_heading}")
        if self.font_weight_body:
            font_parts.append(f"body {self.font_weight_body}")
        if font_parts:
            parts.append("Typography: " + ", ".join(font_parts))
        return ". ".join(parts)
