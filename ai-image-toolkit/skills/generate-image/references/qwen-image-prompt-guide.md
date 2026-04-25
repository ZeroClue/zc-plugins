# Qwen Image Prompt Engineering Guide

Compiled from official Qwen sources:
- Qwen-Image Practical Guide (qwen-image.ai)
- prompt_utils.py from QwenLM/Qwen-Image repo
- Qwen-Image-Edit blog
- Qwen-Image-2512 blog

---

## 1. PROMPT STRUCTURE (Official Template)

The canonical prompt structure from the Qwen team:

```
[Subject] + [Action/Pose] + [Environment] + [Style] +
[Mood/Lighting] + [Technical Specs] + [Additional Details]
```

### Evolution Example
```
Basic:  "A cat"
Better: "A fluffy orange cat sitting on a windowsill"
Best:   "A fluffy orange tabby cat sitting on a vintage wooden windowsill,
         soft morning light streaming through lace curtains, photorealistic style,
         warm color palette, shallow depth of field"
```

---

## 2. TEXT RENDERING IN IMAGES

This is Qwen-Image's standout strength. Key rules:

### Core Text Rules
- **Always enclose exact text in quotes** — e.g., `the sign says "Welcome"`
- **Specify font style**: serif, sans-serif, handwritten, calligraphy, bold, etc.
- **Specify text position explicitly**: "top-left corner", "bottom-right corner", "centered on the sign", "at the top"
- **Specify text size relationships**: main title vs subtitle vs small text
- **Keep text in its original language** — do not translate it
- **Keep original capitalization** of text
- **Never alter or rewrite the user's specified text content**
- **For ambiguous text requests, make them concrete** — e.g., "invitation with name and date" should become specific: invitation bottom reads "Name: Zhang San, Date: July 2025"
- **Do NOT add any extra text beyond what the user explicitly requested** (Chinese prompt optimizer rule 9)

### Text Position/Formatting
- Describe where text goes: "top reads", "bottom reads", "left side shows", "right side displays"
- Describe font attributes: color, size (large, small), weight (bold, light)
- For multiple text elements, describe each separately with position

### Good Text Prompt Examples
```
"A vintage coffee shop sign that says 'The Daily Grind'
 in elegant serif font, weathered wood background,
 morning light casting shadows"
```

```
"Modern tech conference poster with title
 'AI Summit 2024' in bold sans-serif,
 subtitle 'The Future of AI' below in elegant font"
```

```
"Infographic design showing:
 - Main title: 'Climate Change Facts'
 - Three statistics with labels
 - Footer text: 'Source: Environmental Agency 2024'
 Clean, professional layout with data visualization elements"
```

### Multilingual Text
Qwen handles Chinese + English mixed text well:
```
"Traditional Chinese restaurant storefront with neon sign
 saying '美味餐厅' (Delicious Restaurant),
 busy street scene, evening atmosphere"
```

### PPT/Slide/Infographic Text (Qwen-Image-2512)
For complex layouts with lots of text, describe the entire visual layout spatially:
```
"Modern tech slide with deep blue gradient background.
 Title at top center in white bold sans-serif: 'Qwen-Image-2512 Released'.
 Main body is a horizontal comparison...
 Left side shows [X], right side shows [Y].
 Between them, a green streamlined arrow.
 Center label: '2512 Quality Upgrade' in white bold.
 Below the image, three lines of explanation in white text:
 'Bullet point 1...'
 'Bullet point 2...'
 'Bullet point 3...'"
```

---

## 3. THE OFFICIAL PROMPT OPTIMIZER (from prompt_utils.py)

The Qwen team ships an LLM-based prompt optimizer. Here is the full system prompt they use:

### English Optimizer System Prompt
```
You are a Prompt optimizer designed to rewrite user inputs into high-quality Prompts
that are more complete and expressive while preserving the original meaning.

Task Requirements:
1. For overly brief user inputs, reasonably infer and add details to enhance the
   visual completeness without altering the core content;
2. Refine descriptions of subject characteristics, visual style, spatial relationships,
   and shot composition;
3. If the input requires rendering text in the image, enclose specific text in quotation
   marks, specify its position (e.g., top-left corner, bottom-right corner) and style.
   This text should remain unaltered and not translated;
4. Match the Prompt to a precise, niche style aligned with the user's intent.
   If unspecified, choose the most appropriate style (e.g., realistic photography style);
5. Please ensure that the Rewritten Prompt is less than 200 words.
```

After optimization, the Qwen team appends a **magic suffix**:
```
"Ultra HD, 4K, cinematic composition"
```
(Chinese version: "超清，4K，电影级构图")

### Chinese Optimizer — Extra Rules
The Chinese optimizer has additional rules not in the English one:
- Rule 4: Make ambiguous text concrete with specific content
- Rule 5: Auto-select appropriate style (e.g., classical poetry -> Chinese ink wash; realistic photos -> documentary photography)
- Rule 6: For classical Chinese poetry, emphasize Chinese classical elements, avoid Western/modern scenes
- Rule 7: Preserve logical relationships (e.g., food chain arrows)
- **Rule 8: Never use negation words** — if user says "no chopsticks", the prompt should simply not mention chopsticks at all
- **Rule 9: Do NOT add any text content beyond what the user explicitly requested**

### Optimized Prompt Examples (from the repo)

**Example 1 — Art poster with text:**
```
Art poster design: Handwritten calligraphy title "Art Design" in dissolving
particle font, small signature "QwenImage", secondary text "Alibaba".
Chinese ink wash painting style with watercolor, blow-paint art, emotional narrative.
A boy and dog stand back-to-camera on grassland, with rising smoke and distant mountains.
Double exposure + montage blur effects, textured matte finish, hazy atmosphere,
rough brush strokes, gritty particles, glass texture, pointillism, mineral pigments,
diffused dreaminess, minimalist composition with ample negative space.
```

**Example 2 — Character portrait:**
```
Black-haired Chinese adult male, portrait above the collar. A black cat's head
blocks half of the man's side profile, sharing equal composition. Shallow green
jungle background. Graffiti style, clean minimalism, thick strokes. Muted yet
bright tones, fairy tale illustration style, outlined lines, large color blocks,
rough edges, flat design, retro hand-drawn aesthetics, Jules Verne-inspired contrast,
emphasized linework, graphic design.
```

**Example 3 — Fashion/product photo:**
```
Fashion photo of four young models showing phone lanyards. Diverse poses: two
facing camera smiling, two side-view conversing. Casual light-colored outfits
contrast with vibrant lanyards. Minimalist white/grey background. Focus on upper
bodies highlighting lanyard details.
```

**Example 4 — Dynamic scene:**
```
Dynamic lion stone sculpture mid-pounce with front legs airborne and hind legs
pushing off. Smooth lines and defined muscles show power. Faded ancient courtyard
background with trees and stone steps. Weathered surface gives antique look.
Documentary photography style with fine details.
```

---

## 4. EDIT PROMPT OPTIMIZER (from prompt_utils.py)

For image editing, the Qwen team uses a separate, more structured optimizer:

### General Principles
- Keep the enhanced prompt **direct and specific**
- If contradictory/vague/unachievable, prioritize reasonable inference
- Keep core intention unchanged, only enhance clarity and visual feasibility
- All modifications must align with the logic and style of the original image

### Task-Specific Rules

**Add/Delete/Replace:**
- Clear instructions: preserve intent, refine grammar only
- Vague instructions: supplement minimal but sufficient details (category, color, size, orientation, position)
- Remove meaningless instructions (e.g., "Add 0 objects")
- For replacement: "Replace Y with X" and describe key visual features of X

**Text Editing:**
- All text in English double quotes. Keep original language and capitalization.
- Both adding and replacing text are "text replacement" tasks
- Specify position, color, layout only if user requested
- Keep font in original language

**Human/Person Editing:**
- Maintain core visual consistency (ethnicity, gender, age, hairstyle, expression, outfit)
- New elements must be consistent with original style
- Expression/beauty/makeup changes must be **natural and subtle, never exaggerated**

**Style Conversion:**
- Describe style concisely using key visual features
- For colorization/old photo restoration, use fixed template: `"Restore and colorize the photo."`
- Specify the object to be modified clearly
- Place style description at the end if other changes exist

**Inpainting/Outpainting:**
- Inpainting: `"Perform inpainting on this image. The original caption is: "`
- Outpainting: `"Extend the image beyond its boundaries using outpainting. The original caption is: "`

**Multi-Image:**
- Clearly specify which image's element is being modified
- For stylization: describe reference image's style while preserving source content

---

## 5. QWEN-IMAGE-2512 IMPROVEMENTS

The December 2025 update (Qwen-Image-2512) improved:

- **Human realism**: Significantly reduced "AI-generated" look, richer facial details, better environmental context
- **Natural detail**: Finer rendering of landscapes, animal fur, water, foliage textures
- **Text rendering**: Better accuracy, layout, and multimodal (text + image) composition
- **Semantic adherence**: Better follows complex instructions (e.g., "body leaning slightly forward" is now accurately captured)
- **Age rendering**: Properly captures aged facial features (wrinkles, etc.) instead of artificial smoothing

### Implications for Prompting
- Long, detailed prompts with spatial descriptions work well — the model follows them closely
- Grid/multi-panel layouts work well (e.g., 3x4 grid for educational posters)
- Complex infographic/slide layouts with many text elements are achievable
- Describe the full visual composition including background, midground, foreground
- Hair detail keywords are effective: "hair strands distinct", "individual strands with precision"

---

## 6. PROMPT PATTERNS THAT WORK

### Style Specification
Be specific about style rather than vague:
```
GOOD: "Oil painting style specifically like Monet's Water Lilies series,
       impressionist brushstrokes, not photorealistic"
BAD:  "artistic painting"
```

### Negative Prompting
```
Prompt: "Elegant minimalist logo design"
Negative: "complex, busy, cluttered, photorealistic, 3D render"
```

### Power Words (from official guide)
- **Quality**: "highly detailed", "professional", "masterpiece", "ultra-detailed CG"
- **Style**: "in the style of", "inspired by", "aesthetic"
- **Lighting**: "golden hour", "dramatic", "soft diffused", "dappled sunlight"
- **Composition**: "rule of thirds", "centered", "dynamic angle"
- **Technical**: "shallow depth of field", "8K resolution", "32K resolution", "C4D rendering"

### Character Consistency (across scenes)
```
character_description = """
Young woman with short red hair, green eyes,
wearing a blue space suit with orange accents
"""
# Then reuse for each scene:
f"{character_description} piloting a spaceship, determined expression"
f"{character_description} exploring alien planet, amazed expression"
```

### Weighted Elements (attention weighting)
```
"Beautiful landscape with (mountains:1.5), (lake:1.2), (forest:0.8),
 golden hour lighting, ultra detailed, 8k resolution"
```

---

## 7. THINGS TO AVOID

1. **Vague prompts** — "a cat" produces generic results; add specifics
2. **Style confusion** — if you want a specific style, name it precisely; don't leave it ambiguous
3. **Negation words in prompts** (Chinese rule) — Instead of "no chopsticks", just don't mention chopsticks
4. **Untranslated text** — Keep text in the language the user specified; don't translate it during optimization
5. **Adding extra text** — Only include text the user explicitly asked for
6. **Exaggerated expression changes** — For edits, keep expression/beauty changes subtle and natural

---

## 8. COMMON CHALLENGES AND FIXES

| Problem | Fix |
|---------|-----|
| Inconsistent faces | Add: "consistent facial features, symmetrical face, professional portrait photography, sharp focus on face" |
| Wrong text rendering | Be explicit: "The exact text 'Welcome' in Arial Bold font, centered on the sign, no other text visible" |
| Unwanted elements | Use negative prompts: "no people, no text, no watermarks, no logos, clean background" |
| Style confusion | Be specific: "Oil painting style specifically like Monet's Water Lilies series, impressionist brushstrokes, not photorealistic" |
| Ambiguous text | Make concrete: "invitation with name" becomes "底部写着'姓名：张三，日期：2025年7月'" |

---

## 9. COMPLEX LAYOUT EXAMPLES (from Qwen-Image-2512)

### Full Educational Poster (3x4 Grid)
Key technique: Describe each cell individually with time + action + visual details:
```
"Grid of twelve panels in a 3x4 layout, 'A Healthy Day' theme.
Row 1: '06:00 Morning Run' — close-up of woman in grey sportswear, sunrise background;
 '06:30 Stretching' — woman on balcony, pink sky;
 '07:30 Breakfast' — whole wheat bread, avocado, orange juice on table;
 '08:00 Hydration' — glass with lemon slices, sunlight from left...
[continue for all 12 panels]
Natural lighting throughout, warm white and beige tones, layered shadows,
warm lifestyle atmosphere with rhythmic pacing."
```

### Technical Infographic
Key technique: Left-right panels with labeled items:
```
"Professional industrial infographic, deep blue tech background...
Left panel titled 'What Actually Happens' in light blue rounded rect,
 containing three dark blue button-style entries with icons and labels...
Right panel titled 'What Does NOT Happen' in beige rounded rect,
 containing four entries with red X marks over them...
Bottom center: footnote annotation in white small text..."
```

---

## 10. MAGIC SUFFIX

The Qwen team's own prompt optimizer always appends one of these:

- **English**: `"Ultra HD, 4K, cinematic composition"`
- **Chinese**: `"超清，4K，电影级构图"`

This is automatically added after the optimized prompt to boost quality.
