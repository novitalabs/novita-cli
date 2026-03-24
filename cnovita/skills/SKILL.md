---
name: novita
version: 0.2.1
description: >
  CLI for all Novita AI APIs — LLM chat, image generation/editing (Stable Diffusion, FLUX),
  video generation, text-to-speech, speech-to-text, voice cloning, GPU cloud instance management,
  and serverless endpoints. Use this skill whenever the user wants to call Novita AI services,
  generate or edit images, create videos, do TTS/ASR, manage GPU instances, deploy serverless
  workloads, or interact with any novita.ai API. Also trigger when the user mentions the `novita`
  or `cnovita` CLI tool, Novita AI pricing/models/balance, or any task involving the Novita platform.
command: novita
install: pip install cnovita
env:
  NOVITA_API_KEY: required — get one at https://novita.ai/settings/key-management
capabilities:
  - llm-chat
  - llm-completion
  - embeddings
  - rerank
  - text-to-image
  - image-to-image
  - image-inpainting
  - image-upscale
  - remove-background
  - replace-background
  - reimagine
  - cleanup
  - outpainting
  - remove-text
  - image-to-prompt
  - merge-face
  - text-to-video
  - image-to-video
  - text-to-speech
  - glm-text-to-speech
  - speech-to-text
  - voice-cloning
  - model-listing
  - account-management
  - billing-management
  - batch-processing
  - file-management
  - async-task-management
  - gpu-instance-management
  - gpu-templates
  - gpu-clusters
  - network-storage
  - serverless-endpoints
---

# Novita AI CLI

Access all Novita AI APIs from the command line. 95 tests pass (34 unit + 61 E2E, zero mocks).

For the full command reference, read `references/commands.md`.
For verified endpoint coverage, read `references/endpoints.md`.

## Quick Reference

```bash
# LLM
novita chat "Hello" -m deepseek/deepseek-v3-0324
novita embed "text" -m baai/bge-m3
novita rerank "query" -d "doc1" -d "doc2"
novita models list --filter deepseek

# Image generation
novita image flux "a sunset" -W 512 -H 512           # sync, fast
novita image generate "a cat" -W 512 -H 512 --steps 20  # async, SD

# Image editing (sync)
novita image remove-bg photo.jpg -o clean.png
novita image reimagine photo.jpg -o new.png
novita image to-prompt photo.jpg
novita image remove-text photo.jpg -o clean.png
novita image cleanup photo.jpg mask.png -o out.png
novita image outpainting photo.jpg "forest" -W 1536
novita image merge-face face.jpg target.jpg -o merged.png

# Image editing (async)
novita image img2img photo.jpg "watercolor" --strength 0.5
novita image inpainting photo.jpg mask.png "red flower"
novita image upscale photo.jpg --scale 2
novita image replace-bg photo.jpg "beach sunset"

# Video (async)
novita video generate "snow scene" --frames 32
novita video from-image photo.jpg --model SVD-XT
novita video hunyuan "a cat playing piano"

# Audio
novita audio tts "Hello" --voice Calm_Woman -o hello.mp3
novita audio glm-tts "Hello" --voice jam -o hello.wav
novita audio asr recording.wav
novita audio voice-clone https://example.com/voice.mp3

# Account
novita account balance
novita account billing
novita account usage-billing
novita account fixed-billing

# Async task management
novita task status <task_id>
novita task wait <task_id> -o ./results --timeout 300

# Batch & files
novita files upload batch.jsonl
novita files list / get / content / delete <file_id>
novita batch create <file_id>
novita batch list / get / cancel <batch_id>

# GPU instances
novita gpu products / cpu-products / clusters
novita gpu create --product-id xxx --image pytorch:latest --gpu-num 1
novita gpu list / get / start / stop / restart / delete <id>
novita gpu metrics / edit <id>

# Templates
novita template list / get / create / edit / delete

# Storage
novita storage list / create / delete

# Serverless
novita serverless list / get / create / update / delete
```

## Decision Guide

### Which image command?
- **Text -> Image**: `image flux` (fast, sync) or `image generate` (SD, async, more control)
- **Image + Text -> New Image**: `image img2img` (async)
- **Edit part of image**: `image inpainting` (mask + prompt, async) or `image cleanup` (erase masked area, sync)
- **Extend image**: `image outpainting` (sync)
- **Remove elements**: `image remove-bg` (background), `image remove-text` (text overlay)
- **Describe image**: `image to-prompt` (sync)
- **Enlarge image**: `image upscale` (async)
- **Swap face**: `image merge-face` (sync)
- **Restyle**: `image reimagine` (sync)
- **New background**: `image replace-bg` (async)

### Which TTS?
- **English, high quality**: `audio tts` (MiniMax, returns download URL, mp3/wav/flac)
- **Chinese, low latency**: `audio glm-tts` (GLM, returns binary PCM/WAV)

### Sync vs Async?
- **Sync** (result immediately): `flux`, `remove-bg`, `reimagine`, `cleanup`, `outpainting`, `remove-text`, `to-prompt`, `merge-face`
- **Async** (returns task_id, poll with `task wait`): `generate`, `img2img`, `inpainting`, `upscale`, `replace-bg`, all `video` commands

## Common Workflows

### Generate, upscale, and remove background
```bash
novita image flux "product photo" -W 512 -H 512 -o ./tmp
novita image upscale ./tmp/novita_flux_0.png --scale 4 --no-wait
novita task wait <task_id> -o ./results
novita image remove-bg ./results/task_xxx_0.png -o final.png
```

### Batch LLM processing
```bash
novita files upload batch.jsonl
novita batch create <file_id>
novita batch get <batch_id>                    # poll until completed
novita files content <output_file_id> -o results.jsonl
```

### TTS -> ASR round-trip
```bash
novita audio tts "Hello world" -o hello.mp3
novita audio asr hello.mp3
```

## Agent Guidance

- **API Key**: `NOVITA_API_KEY` env var is required. If not set, guide the user to create one at https://novita.ai/settings/key-management. Alternatively pass `--api-key` per-command.
- Use `--json-output` for all machine-readable output
- Use `--no-stream` with chat for complete JSON responses
- For async commands, use `--no-wait` to get task_id, then `novita task wait <id>` for control
- All commands exit with code 1 on error, printing to stderr
- GPU instance creation costs real money — check `novita gpu products` for pricing first
- Template CRUD is free — safe for testing

## Common Errors

- **"API key required"** → Set `NOVITA_API_KEY` env var or pass `--api-key`. Get a key at https://novita.ai/settings/key-management
- **"INSUFFICIENT_RESOURCE"** on GPU create → Try a different `--product-id` or `--billing spot`
- **Task timeout** → Increase `--timeout` value, or use `--no-wait` and poll manually
- **404 on storage/billing APIs** → These endpoints may not be available for all account types
- **GLM TTS returns binary** → Output is raw PCM/WAV audio, saved directly to file (not JSON)
