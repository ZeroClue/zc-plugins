#!/usr/bin/env python3
"""Built-in slide type templates for carousel generation."""

MAGIC_SUFFIX = "Ultra HD, 4K, cinematic composition"


def _brand_style(brand):
    """Extract brand style string from config."""
    if not brand or not brand.data:
        return "Clean modern design, centered layout, sans-serif font, dark background, white text."
    parts = []
    if brand.style_notes:
        parts.append(brand.style_notes)
    if brand.background:
        parts.append(f"background {brand.background}")
    if brand.accent:
        parts.append(f"accent color {brand.accent}")
    if brand.text_primary:
        parts.append(f"text color {brand.text_primary}")
    if brand.text_secondary:
        parts.append(f"secondary text {brand.text_secondary}")
    if brand.font_family:
        weight_h = f" {brand.font_weight_heading}" if brand.font_weight_heading else " Bold"
        weight_b = f" {brand.font_weight_body}" if brand.font_weight_body else " Regular"
        parts.append(f"heading font {brand.font_family}{weight_h}, body font {brand.font_family}{weight_b}")
    return ", ".join(parts) if parts else "Clean modern design, centered layout."


def _canvas_spec(brand, default="1080x1080"):
    size = brand.canvas_size if brand and brand.canvas_size else default
    return f"Canvas size {size} pixels."


def _spacing_rules():
    return (
        "Consistent 24px padding around edges. 16px gap between elements. "
        "Title in top 20% of canvas. Body content in middle 60%. "
        "Footer/CTA in bottom 20%."
    )


def stat_hook(heading, number, text="", brand=None, **kwargs):
    return (
        f"Infographic slide. {_canvas_spec(brand)}\n"
        f"Layout: bold '{number}' in large font centered in upper two-thirds of canvas. "
        f"Supporting text below in smaller font: \"{text}\".\n"
        f"Gradient accent bar (3px tall, full width) separating number and text. "
        f"No other text or decorations.\n"
        f"{_spacing_rules()}\n"
        f"{_brand_style(brand)} "
        f"High contrast, minimal layout. {MAGIC_SUFFIX}"
    )


def statement_hook(heading, text="", brand=None, **kwargs):
    return (
        f"Text-hook infographic slide. {_canvas_spec(brand)}\n"
        f"Layout: bold statement text \"{text or heading}\" centered vertically and horizontally. "
        f"Large heading font, taking up roughly 40% of canvas width. "
        f"No other text, no images, no decorations.\n"
        f"Optional: thin gradient accent line (2px) below the text.\n"
        f"{_spacing_rules()}\n"
        f"{_brand_style(brand)} "
        f"Stark, high contrast, bold typography carries the message. {MAGIC_SUFFIX}"
    )


def checklist(heading, items, icon="checkmark", brand=None, **kwargs):
    item_lines = []
    for i, item in enumerate(items, 1):
        item_lines.append(f"  - ({icon}:1.5) \"{item}\"")
    items_text = "\n".join(item_lines)
    return (
        f"Checklist infographic slide. {_canvas_spec(brand)}\n"
        f"Title: \"{heading}\" in bold heading font, top of canvas.\n"
        f"Vertical list of {len(items)} items, each with a ({icon}:1.5) icon left-aligned:\n"
        f"{items_text}\n"
        f"Each item in a card row with 12px padding. ({icon}:1.5) icon at 24px size, "
        f"text in body font beside it. Number each item sequentially.\n"
        f"{_spacing_rules()}\n"
        f"{_brand_style(brand)} "
        f"Even spacing between rows, left-aligned text, clear numbered layout. {MAGIC_SUFFIX}"
    )


def comparison(heading, columns, brand=None, **kwargs):
    col_parts = []
    for i, col in enumerate(columns):
        col_parts.append(f"Column {i+1}: \"{col}\"")
    cols_text = " | ".join(col_parts)
    return (
        f"Comparison infographic slide. {_canvas_spec(brand)}\n"
        f"Title: \"{heading}\" in bold heading font, top of canvas.\n"
        f"Side-by-side layout with {len(columns)} equal-width columns, "
        f"each in a card container with rounded corners (8px radius) and subtle border.\n"
        f"{cols_text}\n"
        f"Column headers centered within each card. Vertical divider line between columns.\n"
        f"{_spacing_rules()}\n"
        f"{_brand_style(brand)} "
        f"Balanced composition, card-style containers. {MAGIC_SUFFIX}"
    )


def flow(heading, steps, brand=None, **kwargs):
    steps_text = " → ".join(f"\"{s}\"" for s in steps)
    return (
        f"Flow/process infographic slide. {_canvas_spec(brand)}\n"
        f"Title: \"{heading}\" in bold heading font, top of canvas.\n"
        f"Horizontal flow with {len(steps)} steps. Each step in a rounded card "
        f"with step number above and label below. Arrows connecting cards left to right.\n"
        f"Steps: {steps_text}\n"
        f"Cards evenly spaced across canvas width.\n"
        f"{_spacing_rules()}\n"
        f"{_brand_style(brand)} "
        f"Clean directional flow, rounded cards, connecting arrows. {MAGIC_SUFFIX}"
    )


CONTRAST_MODES = {
    "before-after": (
        "Left side: dimmed, desaturated colors, slightly faded or blurred treatment, "
        "conveying 'before' or 'broken'. Right side: sharp, clean, vibrant saturated colors, "
        "conveying 'after' or 'correct'."
    ),
    "good-bad": (
        "Left side: clean, bright, well-organized, positive visual treatment. "
        "Right side: cluttered, dark, disorganized, negative visual treatment."
    ),
    "old-new": (
        "Left side: dated, worn, muted tones, legacy feel. "
        "Right side: modern, fresh, bright colors, contemporary design."
    ),
    "problem-solution": (
        "Left side: stressed, chaotic, red-tinted or dark tones, conveying a problem. "
        "Right side: calm, organized, accent-colored or bright tones, conveying the solution."
    ),
    "light-dark": (
        "Left side: bright, light background, airy treatment. "
        "Right side: dark, moody background, dramatic treatment."
    ),
}


def split(heading, left="", right="", contrast="", brand=None, **kwargs):
    contrast_desc = CONTRAST_MODES.get(contrast, "")
    contrast_section = f"\n{contrast_desc}\n" if contrast_desc else ""
    return (
        f"Split comparison infographic slide. {_canvas_spec(brand)}\n"
        f"Title: \"{heading}\" in bold heading font, top of canvas.\n"
        f"Two halves divided vertically at center, each inside a card container "
        f"with rounded corners (8px radius) and subtle border. "
        f"Left card: \"{left}\". Right card: \"{right}\".\n"
        f"{contrast_section}"
        f"Each card centered within its half-region with 16px internal padding. "
        f"Optional label above each card.\n"
        f"Vertical divider line or 24px gap between cards.\n"
        f"{_spacing_rules()}\n"
        f"{_brand_style(brand)} "
        f"Clear visual contrast between the two sides. {MAGIC_SUFFIX}"
    )


def cta(heading, action_text="", url="", brand=None, **kwargs):
    return (
        f"Call-to-action slide. {_canvas_spec(brand)}\n"
        f"Title: \"{heading}\" in bold heading font, top third.\n"
        f"Centered bold action text: \"{action_text}\" in the middle third, large font. "
        f"This text MUST appear on a SINGLE line — do not break or wrap across lines.\n"
        f"URL below: \"{url}\" in monospace font, bottom third.\n"
        f"Optional gradient accent bar above the action text.\n"
        f"{_spacing_rules()}\n"
        f"{_brand_style(brand)} "
        f"Single focal point, prominent button-style text, minimal design. {MAGIC_SUFFIX}"
    )


def extract_style_prefix(brand):
    """Build a shared style prefix for generate-all consistency.

    Returns a style block derived from brand config that can be prepended
    to every slide's prompt for visual consistency across independent generations.
    """
    parts = ["Consistent visual style across all slides:"]
    if brand and brand.data:
        if brand.style_notes:
            parts.append(brand.style_notes)
        colors = []
        if brand.background:
            colors.append(f"background {brand.background}")
        if brand.accent:
            colors.append(f"accent {brand.accent}")
        if brand.text_primary:
            colors.append(f"primary text {brand.text_primary}")
        if brand.text_secondary:
            colors.append(f"secondary text {brand.text_secondary}")
        if colors:
            parts.append("Colors: " + ", ".join(colors))
        if brand.font_family:
            weight_h = f" {brand.font_weight_heading}" if brand.font_weight_heading else " Bold"
            weight_b = f" {brand.font_weight_body}" if brand.font_weight_body else " Regular"
            parts.append(f"Typography: {brand.font_family}, headings {brand.font_family}{weight_h}, body {brand.font_family}{weight_b}")
    else:
        parts.append("Clean modern design, centered layout, sans-serif font, dark background, white text.")
    return ". ".join(parts) + "."


TEMPLATES = {
    "stat-hook": stat_hook,
    "statement-hook": statement_hook,
    "checklist": checklist,
    "comparison": comparison,
    "flow": flow,
    "split": split,
    "cta": cta,
}


def expand_template(slide_data, brand=None):
    """Expand a typed slide into a full prompt using the template."""
    slide_type = slide_data.get("type", "")
    template_fn = TEMPLATES.get(slide_type)
    if not template_fn:
        return slide_data.get("prompt", "")

    kwargs = {
        "heading": slide_data.get("heading", ""),
        "brand": brand,
        "icon": slide_data.get("icon", "checkmark"),
        "accent": slide_data.get("accent", ""),
    }
    for key in ("items", "columns", "steps", "number", "text", "left", "right",
                "action_text", "url", "contrast"):
        if key in slide_data:
            kwargs[key] = slide_data[key]

    return template_fn(**kwargs)
