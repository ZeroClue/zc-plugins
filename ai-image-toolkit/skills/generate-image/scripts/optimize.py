#!/usr/bin/env python3
"""Prompt optimizer for image generation — expands short prompts into detailed specs."""

import os
import shutil
import subprocess
import sys

MAGIC_SUFFIX = "Ultra HD, 4K, cinematic composition"

OPTIMIZER_SYSTEM_PROMPT = """You are an image generation prompt engineer for the Qwen Image model. Expand the user's short prompt into a detailed prompt optimized for Qwen Image's capabilities.

Qwen Image strengths: exceptional text rendering, complex multi-element layouts, infographic-style compositions, realistic photography.

Rules:
- Text/layout prompts (cards, infographics, stats, UI): expand with exact spatial positioning, font family/weight/size, hex colors for every element, element dimensions, spacing rules, background treatment.
- Photo/illustration prompts: add style, lighting, composition, mood details. If no style specified, default to realistic photography.
- For edit instructions: keep descriptions direct and specific. Preserve the original image's core intention, only enhance clarity and visual feasibility.
- Enclose all text content in double quotes. Specify position and font style for each text element. Never alter or translate the user's text.
- Do NOT add any text the user did not explicitly request. Qwen renders text accurately — hallucinated text will appear in the image.
- Do NOT use negation words. Instead of "no text", just don't mention text. Instead of "no watermark", omit it entirely.
- You may use weighted attention syntax: (element:1.5) to emphasize, (element:0.8) to de-emphasize.
- Output ONLY the expanded prompt — no explanations, no markdown, no prefix.
- {word_cap_instruction}
- Be specific with colors (hex codes), sizes (pixels relative to canvas), and positions (top-left, center, etc.).
- Always end the prompt with: Ultra HD, 4K, cinematic composition
"""

OPTIMIZER_SYSTEM_PROMPT_WITH_BRAND = """You are an image generation prompt engineer for the Qwen Image model. Expand the user's short prompt into a detailed prompt optimized for Qwen Image's capabilities.

Brand config (apply these defaults to every prompt):
{brand_context}

Qwen Image strengths: exceptional text rendering, complex multi-element layouts, infographic-style compositions, realistic photography.

Rules:
- Text/layout prompts (cards, infographics, stats, UI): expand with exact spatial positioning, font family/weight/size, hex colors for every element, element dimensions, spacing rules, background treatment. Use brand colors and fonts above unless the prompt specifies otherwise.
- Photo/illustration prompts: add style, lighting, composition, mood details. If no style specified, default to realistic photography. Apply brand style notes if relevant.
- For edit instructions: keep descriptions direct and specific. Preserve the original image's core intention, only enhance clarity and visual feasibility.
- Enclose all text content in double quotes. Specify position and font style for each text element. Never alter or translate the user's text.
- Do NOT add any text the user did not explicitly request. Qwen renders text accurately — hallucinated text will appear in the image.
- Do NOT use negation words. Instead of "no text", just don't mention text. Instead of "no watermark", omit it entirely.
- You may use weighted attention syntax: (element:1.5) to emphasize, (element:0.8) to de-emphasize.
- Output ONLY the expanded prompt — no explanations, no markdown, no prefix.
- {word_cap_instruction}
- Be specific with colors (hex codes), sizes (pixels relative to canvas), and positions (top-left, center, etc.).
- Always end the prompt with: Ultra HD, 4K, cinematic composition
"""

BATCH_SYSTEM_PROMPT = """You are an image generation prompt engineer for the Qwen Image model. The user will provide {count} numbered prompts. Expand each into a detailed prompt following these rules:

Qwen Image strengths: exceptional text rendering, complex multi-element layouts, infographic-style compositions, realistic photography.

Rules per prompt:
- Text/layout prompts: expand with exact spatial positioning, font family/weight/size, hex colors for every element, element dimensions, spacing rules, background treatment.
- Photo/illustration prompts: add style, lighting, composition, mood details. Default to realistic photography if unspecified.
- Enclose all text content in double quotes with position and font style. Never alter the user's text.
- Do NOT add extra text the user didn't request. Do NOT use negation words.
- {word_cap_instruction}
- Be specific with colors (hex codes), sizes, and positions.
- End each expanded prompt with: Ultra HD, 4K, cinematic composition

Output format — return each expanded prompt on a separate line, prefixed with its number and a colon:
1: <expanded prompt 1>
2: <expanded prompt 2>
...

{brand_section}
"""


def _is_claude_available():
    return shutil.which("claude") is not None


def _is_sdk_available():
    return os.environ.get("ANTHROPIC_API_KEY") is not None


def _word_cap_instruction(max_words):
    if max_words:
        return f"Keep the expanded prompt under {max_words} words."
    return "Use as many words as needed to fully describe the layout."


def _model_id(model):
    mapping = {"haiku": "claude-haiku-4-5-20251001", "sonnet": "claude-sonnet-4-6",
               "opus": "claude-opus-4-7"}
    return mapping.get(model, model)


def _build_system_prompt(brand=None, max_words=500):
    word_cap_instruction = _word_cap_instruction(max_words)
    if brand and brand.data:
        brand_context = "\n".join(f"- {k}: {v}" for k, v in brand.data.items())
        return OPTIMIZER_SYSTEM_PROMPT_WITH_BRAND.format(
            brand_context=brand_context, word_cap_instruction=word_cap_instruction)
    return OPTIMIZER_SYSTEM_PROMPT.format(word_cap_instruction=word_cap_instruction)


def _expand_via_sdk(prompt, model, brand=None, max_words=500):
    try:
        import anthropic
    except ImportError:
        return None
    system = _build_system_prompt(brand, max_words)
    model_id = _model_id(model)
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model_id,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"  SDK error: {e}", file=sys.stderr)
        return None


def _expand_via_claude(prompt, model, brand=None, max_words=500):
    if not shutil.which("claude"):
        return None
    system = _build_system_prompt(brand, max_words)
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


def _expand_via_template(prompt, brand=None):
    text_keywords = ["stat", "chart", "graph", "list", "checklist", "card", "layout",
                     "infographic", "title", "heading", "text", "number", "percent",
                     "compare", "vs", "split", "flow", "step", "cta", "button", "slide"]
    prompt_lower = prompt.lower()
    is_text_layout = any(kw in prompt_lower for kw in text_keywords)

    # Avoid double-suffixing if prompt already ends with it (e.g. from template expansion)
    suffix = "" if prompt.rstrip().endswith(MAGIC_SUFFIX) else f". {MAGIC_SUFFIX}"

    if not is_text_layout:
        result = prompt
        if brand and brand.data:
            result = brand.apply_to_prompt(prompt)
        return f"{result}{suffix}"

    parts = [prompt]
    if brand and brand.data:
        parts.append(brand.apply_to_prompt(""))
        if brand.canvas_size:
            parts.append(f"Canvas: {brand.canvas_size}")
    else:
        parts.append("Clean modern layout, centered composition, clear hierarchy, sans-serif font, bold headings")
    return ". ".join(p for p in parts if p) + suffix


def _validate_expansion(original, expanded):
    """Guard against the optimizer shrinking structured content."""
    if not expanded:
        return original
    if len(expanded) < len(original) * 0.5:
        print(f"  WARNING: optimized prompt shrunk ({len(expanded)} vs {len(original)} chars), using original", file=sys.stderr)
        return original
    return expanded


def optimize_prompt(prompt, brand=None, model="haiku", max_words=500):
    """Expand a short prompt into a detailed image generation spec."""
    # SDK path: fast, but requires ANTHROPIC_API_KEY
    if _is_sdk_available():
        expanded = _expand_via_sdk(prompt, model, brand, max_words)
        if expanded:
            expanded = _validate_expansion(prompt, expanded)
            print(f"  Prompt optimized via SDK ({model}): {len(prompt)} → {len(expanded)} chars", file=sys.stderr)
            return expanded

    # CLI path: works for all Claude Code subscribers (uses their session auth)
    if _is_claude_available():
        expanded = _expand_via_claude(prompt, model, brand, max_words)
        if expanded:
            expanded = _validate_expansion(prompt, expanded)
            print(f"  Prompt optimized via claude CLI ({model}): {len(prompt)} → {len(expanded)} chars", file=sys.stderr)
            return expanded

    print("  SDK and CLI unavailable, using template expansion", file=sys.stderr)
    expanded = _expand_via_template(prompt, brand)
    if expanded != prompt:
        print(f"  Prompt expanded via template: {len(prompt)} → {len(expanded)} chars", file=sys.stderr)
    return expanded


def batch_optimize(prompts, brand=None, model="haiku", max_words=500):
    """Expand multiple prompts in a single API call. Returns list of expanded prompts."""
    if not prompts:
        return []

    brand_section = ""
    if brand and brand.data:
        brand_section = "Brand config to apply:\n" + "\n".join(
            f"- {k}: {v}" for k, v in brand.data.items())

    word_cap_instruction = _word_cap_instruction(max_words)
    system = BATCH_SYSTEM_PROMPT.format(
        count=len(prompts),
        word_cap_instruction=word_cap_instruction,
        brand_section=brand_section,
    )

    numbered = "\n".join(f"{i+1}. {p}" for i, p in enumerate(prompts))

    # Try SDK batch (only if API key available)
    if _is_sdk_available():
        expanded = _batch_via_sdk(numbered, system, model)
        if expanded and len(expanded) == len(prompts):
            expanded = [_validate_expansion(p, e) for p, e in zip(prompts, expanded)]
            print(f"  Batch optimized {len(prompts)} prompts via SDK ({model})", file=sys.stderr)
            return expanded
        if expanded:
            print(f"  Batch SDK returned {len(expanded)} results, expected {len(prompts)} — falling back", file=sys.stderr)

    # Fall back to individual optimization (uses SDK/CLI/template per prompt)
    print("  Optimizing prompts individually", file=sys.stderr)
    return [optimize_prompt(p, brand=brand, model=model, max_words=max_words) for p in prompts]


def _batch_via_sdk(numbered_prompts, system, model):
    try:
        import anthropic
    except ImportError:
        return None
    model_id = _model_id(model)
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model_id,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": numbered_prompts}],
        )
        text = response.content[0].text.strip()
        return _parse_batch_response(text)
    except Exception as e:
        print(f"  Batch SDK error: {e}", file=sys.stderr)
        return None


def _parse_batch_response(text):
    """Parse numbered response lines back into a list."""
    import re
    results = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Match "1: ...", "1. ...", "10) ..." etc.
        m = re.match(r'^(\d+)\s*[:.)]\s*(.*)', line)
        if m:
            results.append(m.group(2).strip())
            continue
        # Continuation of previous entry
        if results:
            results[-1] += " " + line
    return results if results else None
