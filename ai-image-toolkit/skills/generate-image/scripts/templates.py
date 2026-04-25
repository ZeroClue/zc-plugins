#!/usr/bin/env python3
"""Built-in slide type templates for carousel generation."""


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
    if brand.font_family:
        parts.append(f"font {brand.font_family}")
    return ", ".join(parts) if parts else "Clean modern design, centered layout."


def stat_hook(heading, number, text="", brand=None, **kwargs):
    big_stat_prompt = (
        f"Infographic slide. {heading}. "
        f"Large bold number '{number}' centered in the upper two-thirds. "
        f"Smaller supporting text below: '{text}'. "
        f"{_brand_style(brand)} "
        f"Minimal layout, no decorations, high contrast."
    )
    return big_stat_prompt


def checklist(heading, items, icon="checkmark", brand=None, **kwargs):
    item_lines = []
    for i, item in enumerate(items, 1):
        item_lines.append(f"{i}. {icon} {item}")
    items_text = "\n".join(item_lines)
    return (
        f"Checklist infographic slide. Title: '{heading}'. "
        f"Vertical list of {len(items)} items, each with a {icon} icon on the left:\n"
        f"{items_text}\n"
        f"{_brand_style(brand)} "
        f"Even spacing between items, left-aligned text, clear numbered layout."
    )


def comparison(heading, columns, brand=None, **kwargs):
    col_parts = []
    for i, col in enumerate(columns):
        col_parts.append(f"Column {i+1}: {col}")
    cols_text = " | ".join(col_parts)
    return (
        f"Comparison infographic slide. Title: '{heading}'. "
        f"Side-by-side layout with {len(columns)} equal-width columns. "
        f"{cols_text} "
        f"{_brand_style(brand)} "
        f"Card-style containers with subtle borders, centered headers per column."
    )


def flow(heading, steps, brand=None, **kwargs):
    steps_text = " → ".join(f"Step {i+1}: {s}" for i, s in enumerate(steps))
    return (
        f"Flow/process infographic slide. Title: '{heading}'. "
        f"Horizontal flow with {len(steps)} steps connected by arrows. "
        f"{steps_text} "
        f"{_brand_style(brand)} "
        f"Each step in a rounded card or circle, arrows between them, left to right."
    )


def split(heading, left="", right="", brand=None, **kwargs):
    return (
        f"Split comparison infographic slide. Title: '{heading}'. "
        f"Two halves divided vertically. Left side: '{left}'. Right side: '{right}'. "
        f"{_brand_style(brand)} "
        f"Clear visual contrast between the two sides, centered text in each half."
    )


def cta(heading, action_text="", url="", brand=None, **kwargs):
    return (
        f"Call-to-action slide. Title: '{heading}'. "
        f"Centered bold action text: '{action_text}'. "
        f"URL displayed below: '{url}'. "
        f"{_brand_style(brand)} "
        f"Single focal point, prominent button-style text, clean minimal design."
    )


TEMPLATES = {
    "stat-hook": stat_hook,
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
    if "items" in slide_data:
        kwargs["items"] = slide_data["items"]
    if "columns" in slide_data:
        kwargs["columns"] = slide_data["columns"]
    if "steps" in slide_data:
        kwargs["steps"] = slide_data["steps"]
    if "number" in slide_data:
        kwargs["number"] = slide_data["number"]
    if "text" in slide_data:
        kwargs["text"] = slide_data["text"]
    if "left" in slide_data:
        kwargs["left"] = slide_data["left"]
    if "right" in slide_data:
        kwargs["right"] = slide_data["right"]
    if "action_text" in slide_data:
        kwargs["action_text"] = slide_data["action_text"]
    if "url" in slide_data:
        kwargs["url"] = slide_data["url"]

    return template_fn(**kwargs)
