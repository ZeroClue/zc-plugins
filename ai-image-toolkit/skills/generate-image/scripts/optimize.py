#!/usr/bin/env python3
"""Prompt optimizer for image generation — expands short prompts into detailed specs."""

import shutil
import subprocess
import sys

OPTIMIZER_SYSTEM_PROMPT = """You are an image generation prompt engineer. Expand the user's short prompt into a detailed, specific image generation prompt suitable for an AI image model.

Rules:
- If the prompt describes text, layout, cards, infographics, stats, or UI: expand with exact spatial positioning, font family/weight/size, hex colors for every element, element dimensions, spacing rules, and background treatment.
- If the prompt describes an illustration or photo: add style, lighting, composition, and mood details. Keep it natural.
- Output ONLY the expanded prompt — no explanations, no markdown, no prefix.
- Keep the expanded prompt under 400 words.
- Be specific with colors (use hex codes), sizes (in pixels relative to canvas), and positions (top-left, center, etc.).
"""

OPTIMIZER_SYSTEM_PROMPT_WITH_BRAND = """You are an image generation prompt engineer. Expand the user's short prompt into a detailed, specific image generation prompt suitable for an AI image model.

Brand config (apply these defaults to every prompt):
{brand_context}

Rules:
- If the prompt describes text, layout, cards, infographics, stats, or UI: expand with exact spatial positioning, font family/weight/size, hex colors for every element, element dimensions, spacing rules, and background treatment. Use brand colors and fonts above unless the prompt specifies otherwise.
- If the prompt describes an illustration or photo: add style, lighting, composition, and mood details. Keep it natural. Apply brand style notes if relevant.
- Output ONLY the expanded prompt — no explanations, no markdown, no prefix.
- Keep the expanded prompt under 400 words.
- Be specific with colors (use hex codes), sizes (in pixels relative to canvas), and positions (top-left, center, etc.).
"""


def _is_claude_available():
    return shutil.which("claude") is not None


def _expand_via_claude(prompt, model, brand_config=None):
    system = OPTIMIZER_SYSTEM_PROMPT
    if brand_config and brand_config.data:
        brand_context = "\n".join(f"- {k}: {v}" for k, v in brand_config.data.items())
        system = OPTIMIZER_SYSTEM_PROMPT_WITH_BRAND.format(brand_context=brand_context)

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--system-prompt", system, "--model", model],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _expand_via_template(prompt, brand_config=None):
    text_keywords = ["stat", "chart", "graph", "list", "checklist", "card", "layout",
                     "infographic", "title", "heading", "text", "number", "percent",
                     "compare", "vs", "split", "flow", "step", "cta", "button", "slide"]
    prompt_lower = prompt.lower()
    is_text_layout = any(kw in prompt_lower for kw in text_keywords)

    if not is_text_layout:
        if brand_config and brand_config.data:
            return brand_config.apply_to_prompt(prompt)
        return prompt

    parts = [prompt]
    if brand_config and brand_config.data:
        parts.append(brand_config.apply_to_prompt(""))
        if brand_config.canvas_size:
            parts.append(f"Canvas: {brand_config.canvas_size}")
    else:
        parts.append("Clean modern layout, centered composition, clear hierarchy, sans-serif font, bold headings")
    return ". ".join(p for p in parts if p)


def optimize_prompt(prompt, brand=None, model="haiku"):
    """Expand a short prompt into a detailed image generation spec."""
    if _is_claude_available():
        expanded = _expand_via_claude(prompt, model, brand)
        if expanded:
            print(f"  Prompt optimized via claude ({model}): {len(prompt)} → {len(expanded)} chars", file=sys.stderr)
            return expanded
        print("  claude CLI failed, falling back to template expansion", file=sys.stderr)
    else:
        print("  claude CLI not found, using template expansion", file=sys.stderr)

    expanded = _expand_via_template(prompt, brand)
    if expanded != prompt:
        print(f"  Prompt expanded via template: {len(prompt)} → {len(expanded)} chars", file=sys.stderr)
    return expanded
