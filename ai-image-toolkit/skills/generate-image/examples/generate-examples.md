# Generate Image Examples

## Simple text-to-image

User: "Generate an image of a cat sitting on a windowsill"

```bash
python3 skills/generate-image/scripts/generate.py generate "a cat sitting on a windowsill"
```

Output: `cat_sitting_on_a_windowsill_20260423_143022.png` in current directory.

## Dimension-aware generation

User: "Make a 1920x1080 cyberpunk cityscape, full quality"

```bash
python3 skills/generate-image/scripts/generate.py generate "cyberpunk cityscape" --width 1920 --height 1080 --steps 50
```

Dimensions extracted from prompt, "full quality" mapped to `--steps 50`.

## Generate with seed for reproducibility

User: "Render a mountain landscape with seed 42"

```bash
python3 skills/generate-image/scripts/generate.py generate "mountain landscape" --seed 42
```

## Save to specific location

User: "Create an image of a sunset and save it to /tmp/output"

```bash
python3 skills/generate-image/scripts/generate.py generate "sunset" --output-dir /tmp/output
```

## Edit with source image

User: "Remove the background from this photo: /home/user/photo.png"

```bash
python3 skills/generate-image/scripts/generate.py edit "remove the background" --image /home/user/photo.png
```

## Edit with reference image

User: "Make this photo look like the style of this reference: photo.jpg using reference: style.jpg"

```bash
python3 skills/generate-image/scripts/generate.py edit "apply the style of the reference image" --image photo.jpg --reference-image style.jpg
```

## Handle timeout with async retry

If a sync call times out (cold start), retry with async:

```bash
python3 skills/generate-image/scripts/generate.py generate "a dragon in a forest" --async
```

The script submits the job and polls every 3 seconds until completion.
