# RunPod Setup Guide

This plugin uses [RunPod](https://runpod.io?ref=lnnwdl3q) serverless endpoints to run Qwen Image models. You need a RunPod account, two serverless endpoints deployed, and three environment variables set.

## What you need

- A RunPod account ([sign up here](https://runpod.io?ref=lnnwdl3q))
- Two serverless endpoints deployed from the worker repos below
- Your RunPod API key

## Step 1: Deploy the endpoints

Two ComfyUI worker repos power this plugin. Deploy each as a serverless endpoint on RunPod.

### Text-to-image (Qwen Image 2512)

- **Repo:** [ZeroClue/qwen-img-2512](https://github.com/ZeroClue/qwen-img-2512)
- **Deploy on RunPod:** *(link coming soon — will be added once published on Serverless Hub)*

### Image editing (Qwen Image Edit 2511)

- **Repo:** [ZeroClue/qwen-img-edit-2511](https://github.com/ZeroClue/qwen-img-edit-2511)
- **Deploy on RunPod:** *(link coming soon — will be added once published on Serverless Hub)*

Follow the README in each repo for deployment instructions. Both use the same pattern: fork the repo, create a serverless endpoint on RunPod pointing to it, and wait for the build to complete.

## Step 2: Get your credentials

1. **Endpoint IDs**: RunPod dashboard > Serverless > click each endpoint > copy the endpoint ID from the URL or settings
2. **API key**: RunPod dashboard > Settings > API Keys

## Step 3: Set environment variables

The script auto-loads a `.env` file from your project root, so the easiest option is:

```bash
# Create .env in your project root
echo 'RUNPOD_2512_ENDPOINT_ID=your-text-to-image-endpoint-id' >> .env
echo 'RUNPOD_EDIT_ENDPOINT_ID=your-image-edit-endpoint-id' >> .env
echo 'RUNPOD_API_KEY=your-api-key' >> .env
```

Or export them in your shell:

```bash
export RUNPOD_2512_ENDPOINT_ID="your-text-to-image-endpoint-id"
export RUNPOD_EDIT_ENDPOINT_ID="your-image-edit-endpoint-id"
export RUNPOD_API_KEY="your-api-key"
```

The plugin reads these on every invocation. If any are missing, it will tell you which ones.

## GPU requirements

- **Qwen Image 2512**: NVIDIA GPU with 24GB+ VRAM (e.g. RTX 4090, A5000, A100)
- **Qwen Image Edit 2511**: Same requirements

Both endpoints use fp8 quantized models to fit in 24GB.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| First request times out | Cold start — wait 30-120s or retry |
| HTTP 401/403 | Wrong API key — check dashboard |
| HTTP 404 | Wrong endpoint ID — verify in dashboard |
| Out of memory | Switch to a GPU with more VRAM |

For detailed API documentation, see `references/endpoints.md`.
