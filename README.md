# cnovita

CLI for all Novita AI APIs — LLM chat, images, video, audio, GPU instances, serverless endpoints, and more.

## Get Started

**CLI:**
```bash
pip install cnovita
```

**Skill:**
```bash
npx skills add jaxzhang-novita/cnovita
```

**Agent:**
```
Install cnovita by `npx skills add jaxzhang-novita/cnovita` and tell me how to use it
```

## API Key

An API key is required. Get one at: **https://novita.ai/settings/key-management**

```bash
export NOVITA_API_KEY="sk_..."
```

Or pass it per-command: `novita --api-key sk_... chat "Hello"`

## Quick Start

```bash
# Chat with LLM
novita chat "What is Python?" -m deepseek/deepseek-v3-0324

# Generate an image
novita image flux "a sunset over mountains" -W 512 -H 512

# Image editing
novita image reimagine photo.jpg -o reimagined.png
novita image remove-bg photo.jpg -o clean.png
novita image to-prompt photo.jpg

# Text to speech
novita audio tts "Hello world" --voice Calm_Woman -o hello.mp3

# Speech to text
novita audio asr recording.wav

# List GPU products
novita gpu products

# Check account balance
novita account balance
```

## Command Groups

| Command | Description |
|---------|-------------|
| `novita chat` | LLM chat completion (streaming) |
| `novita complete` | Text completion |
| `novita embed` | Text embeddings |
| `novita rerank` | Document reranking |
| `novita models` | List/get models |
| `novita image generate` | Stable Diffusion txt2img (async) |
| `novita image flux` | FLUX.1 Schnell (sync) |
| `novita image img2img` | Image-to-image generation (async) |
| `novita image inpainting` | Inpaint masked regions (async) |
| `novita image upscale` | Image upscaling (async) |
| `novita image remove-bg` | Background removal (sync) |
| `novita image replace-bg` | Background replacement (async) |
| `novita image reimagine` | Reimagine an image (sync) |
| `novita image cleanup` | Erase masked region (sync) |
| `novita image outpainting` | Extend image borders (sync) |
| `novita image remove-text` | Remove text from image (sync) |
| `novita image to-prompt` | Image to text description (sync) |
| `novita image merge-face` | Face merging (sync) |
| `novita video generate` | Text-to-video (async) |
| `novita video from-image` | Image-to-video (async) |
| `novita video hunyuan` | Hunyuan video (async) |
| `novita audio tts` | Text-to-speech (MiniMax) |
| `novita audio glm-tts` | Text-to-speech (GLM) |
| `novita audio asr` | Speech-to-text |
| `novita audio voice-clone` | Voice cloning (MiniMax) |
| `novita account balance` | Account balance |
| `novita account billing` | Monthly billing |
| `novita account usage-billing` | Usage-based billing |
| `novita account fixed-billing` | Fixed-term billing |
| `novita task status` | Check async task |
| `novita task wait` | Wait for async task |
| `novita batch` | Batch processing |
| `novita files` | File management (upload/list/get/delete) |
| `novita gpu` | GPU instance management |
| `novita gpu clusters` | List data centers |
| `novita template` | GPU templates (CRUD) |
| `novita storage` | Network storage management |
| `novita serverless` | Serverless endpoints |

## JSON Output

Add `--json-output` for machine-readable output:

```bash
novita --json-output chat "Hello" --no-stream
novita --json-output models list
novita --json-output account balance
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT
