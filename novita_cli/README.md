# Novita AI CLI

Command-line interface for major Novita AI APIs: LLM chat, embeddings, image generation, video, audio, and more.

## Installation

```bash
pip install novita-cli
```

This installs the `novita` command.

## Configuration

Set your API key:
```bash
export NOVITA_API_KEY="your-key-here"
```

Or pass it per-command:
```bash
novita --api-key sk_xxx chat "Hello"
```

## Commands

### LLM

```bash
# Chat (streaming by default)
novita chat "What is Python?" -m deepseek/deepseek-v3-0324
novita chat "Explain gravity" --system "You are a physics teacher" --max-tokens 500

# Text completion
novita complete "Once upon a time"

# Embeddings
novita embed "Hello world" -m baai/bge-m3

# Rerank documents
novita rerank "best pet" -d "cats are cute" -d "dogs are loyal" -d "fish swim"
```

### Models

```bash
novita models list                     # List all models
novita models list --filter deepseek   # Filter by name
novita models get deepseek/deepseek-r1 # Get model details
```

### Images

```bash
# Stable Diffusion text-to-image
novita image generate "a cute cat" -W 512 -H 512 --steps 20

# FLUX.1 Schnell (fast, synchronous)
novita image flux "a sunset over mountains"

# Upscale
novita image upscale photo.jpg --scale 2

# Remove background (sync)
novita image remove-bg photo.jpg -o clean.png
```

### Video

```bash
# Text-to-video
novita video generate "a girl walking in snow" --frames 32

# Image-to-video
novita video from-image photo.jpg --model SVD-XT

# Hunyuan Video
novita video hunyuan "a cat playing piano"
```

### Audio

```bash
# Text-to-speech
novita audio tts "Hello world" --voice Calm_Woman -o hello.mp3

# Speech-to-text
novita audio asr recording.wav
```

### Account

```bash
novita account balance    # Check credit balance
novita account billing    # View monthly bills
```

### Tasks (async)

```bash
novita task status <task_id>           # Check task status
novita task wait <task_id> -o ./out    # Wait and download results
```

### Batch

```bash
novita batch create <file_id>   # Create batch job
novita batch list               # List batches
novita batch get <batch_id>     # Get batch details
novita batch cancel <batch_id>  # Cancel batch
```

### GPU Instances

```bash
# List available GPU products
novita gpu products
novita gpu products --gpu-num 1

# List your instances
novita gpu list
novita gpu list --status running

# Create a GPU instance
novita gpu create --product-id 4090.16c125g --image pytorch/pytorch:latest --gpu-num 1

# Manage instances
novita gpu get <instance_id>
novita gpu start <instance_id>
novita gpu stop <instance_id>
novita gpu delete <instance_id>

# View metrics
novita gpu metrics <instance_id>

# Edit instance (expand disk, change ports)
novita gpu edit <instance_id> --expand-disk 50

# CPU products
novita gpu cpu-products
```

### Templates

```bash
novita template list --channel official   # Browse official templates
novita template list --channel private    # Your private templates
novita template get <template_id>
novita template create --name mytempl --image pytorch/pytorch:latest
novita template delete <template_id>
```

### Serverless Endpoints

```bash
# List endpoints
novita serverless list

# Create a serverless endpoint
novita serverless create --image myimage:latest --port 8080 --product-id xxx

# Manage endpoints
novita serverless get <endpoint_id>
novita serverless update <endpoint_id> --max-workers 3
novita serverless delete <endpoint_id>
```

## JSON Output

Add `--json-output` for machine-readable JSON:
```bash
novita --json-output chat "Hello" --no-stream
novita --json-output models list
novita --json-output account balance
```

## Async Tasks

Image/video generation commands return a task ID. By default, the CLI polls and downloads results. Use `--no-wait` to get just the task ID:
```bash
novita image generate "a dog" --no-wait
# Task ID: abc123-def456

novita task wait abc123-def456 -o ./results
```
