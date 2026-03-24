# cnovita

CLI for all Novita AI APIs — LLM chat, images, video, audio, GPU instances, serverless endpoints, and more.

## Install

```bash
pip install cnovita
```

## Setup

```bash
export NOVITA_API_KEY="your-key-here"
```

## Quick Start

```bash
# Chat with LLM
novita chat "What is Python?" -m deepseek/deepseek-v3-0324

# Generate an image
novita image flux "a sunset over mountains" -W 512 -H 512

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
| `novita image upscale` | Image upscaling (async) |
| `novita image remove-bg` | Background removal (sync) |
| `novita video generate` | Text-to-video (async) |
| `novita video from-image` | Image-to-video (async) |
| `novita video hunyuan` | Hunyuan video (async) |
| `novita audio tts` | Text-to-speech |
| `novita audio asr` | Speech-to-text |
| `novita account balance` | Account balance |
| `novita account billing` | Monthly billing |
| `novita task status` | Check async task |
| `novita task wait` | Wait for async task |
| `novita batch` | Batch processing |
| `novita gpu` | GPU instance management |
| `novita template` | GPU templates |
| `novita serverless` | Serverless endpoints |

## JSON Output

Add `--json-output` for machine-readable output:

```bash
novita --json-output chat "Hello" --no-stream
novita --json-output models list
novita --json-output account balance
```

## License

MIT
