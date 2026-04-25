# RunPod API Reference

## Endpoints

### Text-to-Image (Qwen Image 2512)

```
POST https://api.runpod.ai/v2/{RUNPOD_2512_ENDPOINT_ID}/runsync
```

**Input schema:**
```json
{
  "input": {
    "prompt": "text description",
    "width": 1328,
    "height": 1328,
    "steps": 4,
    "seed": null,
    "negative_prompt": "",
    "batch_size": 1,
    "cfg": null,
    "shift": null,
    "sampler": null,
    "scheduler": null,
    "lora": null
  }
}
```

**Width/height:** 256-4096 per dimension. Default 1328x1328.
**Steps:** 4 = 4-step Lightning (LoRA, CFG=1, ~2s). 5-8 = 8-step Lightning (LoRA, CFG=1, ~4-8s). 9+ = full quality (no LoRA, CFG=4, ~15-30s). Auto-selects LoRA from step count.
**Seed:** Omit for random. Include for reproducibility.
**cfg:** Override CFG scale. Auto: 1.0 for Lightning, 4.0 for base.
**shift:** ModelSamplingAuraFlow shift. Default 3.1. Increase if blurry/dark, decrease for more detail.
**sampler:** KSampler sampler name. Default `euler`. Alternatives: `res_multistep`, etc.
**scheduler:** KSampler scheduler name. Default `simple`.
**lora:** Override LoRA selection. `4step`, `8step`, or `none`. Auto-selected from steps when omitted.

### Image Editing (Qwen Image Edit 2511)

```
POST https://api.runpod.ai/v2/{RUNPOD_EDIT_ENDPOINT_ID}/runsync
```

**Input schema:**
```json
{
  "input": {
    "prompt": "edit instruction",
    "image": "base64-encoded source image",
    "reference_image": "base64-encoded reference image (optional)",
    "steps": 4,
    "seed": null,
    "negative_prompt": "",
    "cfg": null,
    "shift": null,
    "sampler": null,
    "scheduler": null,
    "lora": null
  }
}
```

**No width/height** — output dimensions inherit from source image.
**Steps:** 4 = 4-step Lightning (LoRA, CFG=1, ~2-5s). 5-8 = 8-step Lightning (LoRA, CFG=1). 40 = full quality (no LoRA, CFG=4, ~15-30s). Auto-selects LoRA from step count.
**Single vs dual image:** If no `reference_image` provided, source image is reused (single-image edit).
**cfg, shift, sampler, scheduler, lora:** Same as generate endpoint.

## Response Format

Both endpoints return:
```json
{
  "status": "COMPLETED",
  "output": {
    "images": [
      {"data": "base64-encoded PNG", "filename": "image.png"}
    ]
  }
}
```

The `images` array may contain multiple entries when `batch_size > 1`.

## Async Mode

For longer jobs or cold starts, use async:

```
POST https://api.runpod.ai/v2/{endpoint_id}/run          # submit → {"id": "job-id", "status": "IN_QUEUE"}
GET  https://api.runpod.ai/v2/{endpoint_id}/status/{id}  # poll → {"status": "IN_PROGRESS"} or {"status": "COMPLETED", ...}
```

Poll every 3 seconds. Status values: `IN_QUEUE`, `IN_PROGRESS`, `COMPLETED`, `FAILED`.

## Cold Start Behavior

Serverless endpoints spin down after idle. First request after idle period triggers a cold start:
- Duration: 30-120 seconds depending on model size
- Symptom: `runsync` may timeout, async returns `IN_QUEUE` for longer
- Mitigation: Use async mode, or retry once after timeout

## Error Responses

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 401 | Invalid API key | Check `RUNPOD_API_KEY` |
| 403 | Forbidden — wrong account | Verify endpoint ownership |
| 404 | Endpoint not found | Check endpoint ID |
| 429 | Rate limited | Wait and retry |
| 500 | Handler error | Check payload, retry once |
| 504 | Gateway timeout | Use async mode |

## ComfyUI Workflow Mapping

The script's simplified input maps to a ComfyUI workflow with these key node IDs:

### Generate (2512) nodes:
- `"238:227"` — positive text encode
- `"238:229"` — switch (Lightning/full quality toggle via PrimitiveBoolean)

### Edit (2511) nodes:
- `"41"` — source image loader
- `"83"` — reference image loader
- `"170:151"` — positive prompt
- `"170:149"` — negative prompt
- `"170:169"` — KSampler seed
- `"170:168"` — switch boolean

The switch pattern: `PrimitiveBoolean` node feeds three `Switch` nodes that select model/LoRA, steps, and CFG based on whether steps <= 4 (Lightning) or higher (full quality).
