---
name: novita
version: 0.2.0
description: CLI for all Novita AI APIs - LLM, images, video, audio, GPU, serverless
command: novita
install: pip install -e agent-harness/
env:
  NOVITA_API_KEY: required
tests:
  unit: 34 passed
  e2e: 61 passed (all real API calls, zero mocks)
  total: 95 passed (100%)
  lifecycles:
    - "GPU Instance: CREATE -> GET -> LIST -> DELETE (spot, multi-product fallback)"
    - "Template: CREATE -> GET -> LIST -> CLI GET -> EDIT -> DELETE -> verify gone"
    - "Batch: upload JSONL -> CREATE -> GET -> LIST -> cancel"
    - "Files: upload -> get -> delete"
    - "Async Image: generate --no-wait -> task status -> task wait -> download"
    - "Image Upscale: FLUX -> download -> upscale --no-wait -> poll -> verify"
    - "Image Remove-BG: FLUX -> download -> remove-bg -> verify output file"
    - "Image Editing: FLUX -> to-prompt / reimagine / remove-text"
    - "Audio Round-Trip: TTS -> download -> ASR -> verify transcript"
    - "Task API: submit -> status -> poll -> complete"
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

Access all Novita AI APIs from the command line.

## Command Groups

### `novita chat <message>` - LLM Chat
Send chat completion requests with streaming support.
```bash
novita chat "What is Python?" -m deepseek/deepseek-v3-0324
novita chat "Explain gravity" --system "Be brief" --max-tokens 100
novita --json-output chat "Hello" --no-stream
```
**Options:** `-m/--model`, `--system`, `--max-tokens`, `--temperature`, `--top-p`, `--stream/--no-stream`, `--json-schema`

### `novita complete <prompt>` - Text Completion
```bash
novita complete "Once upon a time" --max-tokens 200
```

### `novita embed <text>` - Embeddings
```bash
novita embed "Hello world" -m baai/bge-m3
```

### `novita rerank <query>` - Rerank Documents
```bash
novita rerank "best pet" -d "cats are cute" -d "dogs are loyal"
```

### `novita models list` - List Models
```bash
novita models list --filter deepseek
novita models get deepseek/deepseek-r1
```

### `novita image generate <prompt>` - Text-to-Image (SD)
```bash
novita image generate "a cute cat" -W 512 -H 512 --steps 20
novita image generate "landscape" --sampler "DPM++ 2M Karras" --cfg 7.5
```
**Options:** `-m`, `-W`, `-H`, `-n`, `--steps`, `--cfg`, `--sampler`, `--negative`, `--seed`, `-o`, `--format`, `--no-wait`

### `novita image flux <prompt>` - FLUX.1 Schnell (sync)
```bash
novita image flux "a sunset" -W 512 -H 512
```

### `novita image img2img <image> <prompt>` - Image-to-Image
```bash
novita image img2img photo.jpg "make it watercolor" --strength 0.5
```
**Options:** `-m`, `-W`, `-H`, `-n`, `--steps`, `--cfg`, `--sampler`, `--strength`, `--negative`, `--seed`, `-o`, `--no-wait`

### `novita image inpainting <image> <mask> <prompt>` - Inpainting
```bash
novita image inpainting photo.jpg mask.png "a red flower" --steps 20
```

### `novita image upscale <path>` - Image Upscale
```bash
novita image upscale photo.jpg --scale 2
```

### `novita image remove-bg <path>` - Remove Background (sync)
```bash
novita image remove-bg photo.jpg -o clean.png
```

### `novita image replace-bg <image> <prompt>` - Replace Background (async)
```bash
novita image replace-bg photo.jpg "a beach sunset"
```

### `novita image reimagine <image>` - Reimagine (sync)
```bash
novita image reimagine photo.jpg -o reimagined.png
```

### `novita image cleanup <image> <mask>` - Cleanup / Erase (sync)
```bash
novita image cleanup photo.jpg mask.png -o cleaned.png
```

### `novita image outpainting <image> <prompt>` - Outpainting (sync)
```bash
novita image outpainting photo.jpg "forest landscape" -W 1536 -H 1024
```

### `novita image remove-text <image>` - Remove Text (sync)
```bash
novita image remove-text photo.jpg -o clean.png
```

### `novita image to-prompt <image>` - Image to Prompt (sync)
```bash
novita image to-prompt photo.jpg
```

### `novita image merge-face <face> <target>` - Merge Face (sync)
```bash
novita image merge-face face.jpg target.jpg -o merged.png
```

### `novita video generate <prompt>` - Text-to-Video
```bash
novita video generate "a girl walking in snow" --frames 32
```

### `novita video from-image <path>` - Image-to-Video
```bash
novita video from-image photo.jpg --model SVD-XT
```

### `novita video hunyuan <prompt>` - Hunyuan Video
```bash
novita video hunyuan "a cat playing piano"
```

### `novita audio tts <text>` - Text-to-Speech (MiniMax)
```bash
novita audio tts "Hello world" --voice Calm_Woman -o hello.mp3
```
**Voices:** Wise_Woman, Friendly_Person, Calm_Woman, Deep_Voice_Man, Lively_Girl, Young_Knight, and more.

### `novita audio glm-tts <text>` - GLM TTS
```bash
novita audio glm-tts "Hello" --voice jam -o hello.wav
```
**Voices:** tongtong, chuichui, xiaochen, jam, kazi, douji, luodo

### `novita audio asr <source>` - Speech-to-Text
```bash
novita audio asr recording.wav
novita audio asr https://example.com/audio.mp3
```

### `novita audio voice-clone <audio_url>` - Voice Cloning (MiniMax)
```bash
novita audio voice-clone https://example.com/voice.mp3 --text "preview text"
```

### `novita account balance` - Account Balance
```bash
novita account balance
```

### `novita account billing` - Monthly Bills
```bash
novita account billing
```

### `novita account usage-billing` - Usage-Based Billing
```bash
novita account usage-billing
```

### `novita account fixed-billing` - Fixed-Term Billing
```bash
novita account fixed-billing
```

### `novita task status <id>` - Check Task
```bash
novita task status abc123-def456
```

### `novita task wait <id>` - Wait & Download
```bash
novita task wait abc123-def456 -o ./results --timeout 300
```

### `novita batch create/list/get/cancel` - Batch Jobs
```bash
novita batch create <file_id>
novita batch list
novita batch get <batch_id>
novita batch cancel <batch_id>
```

### `novita files` - File Management
```bash
novita files upload batch_input.jsonl
novita files list
novita files get <file_id>
novita files content <file_id>
novita files delete <file_id>
```

### `novita gpu` - GPU Instance Management
```bash
novita gpu products                    # List available GPUs
novita gpu cpu-products                # List CPU products
novita gpu clusters                    # List data centers
novita gpu list                        # List your instances
novita gpu create --product-id xxx --image pytorch:latest --gpu-num 1
novita gpu get <id>                    # Instance details
novita gpu start <id>                  # Start instance
novita gpu stop <id>                   # Stop instance
novita gpu restart <id>                # Restart instance
novita gpu delete <id>                 # Delete instance
novita gpu metrics <id>                # View metrics
novita gpu edit <id> --expand-disk 50  # Edit instance
```

### `novita template` - GPU Templates
```bash
novita template list --channel official
novita template get <id>
novita template create --name mytempl --image pytorch:latest
novita template edit <id> --name "new-name"
novita template delete <id>
```

### `novita storage` - Network Storage
```bash
novita storage list
novita storage create --cluster-id cl-xxx --name mydata --size 100
novita storage delete <id>
```

### `novita serverless` - Serverless Endpoints
```bash
novita serverless list
novita serverless create --image myimage:latest --port 8080 --product-id xxx
novita serverless get <id>
novita serverless update <id> --max-workers 3
novita serverless delete <id>
```

## Agent Guidance

- Use `--json-output` for all machine-readable output
- Use `--no-stream` with chat for complete JSON responses
- Async image/video commands return task IDs; use `--no-wait` + `novita task wait` for control
- Sync image commands: `remove-bg`, `reimagine`, `cleanup`, `outpainting`, `remove-text`, `to-prompt`, `merge-face`, `flux`
- Async image commands: `generate`, `img2img`, `inpainting`, `upscale`, `replace-bg`
- All commands exit with code 1 on error, printing to stderr
- GPU instance creation costs real money - use `novita gpu products` to check pricing first
- Template CRUD is free - use for testing instance configurations
- The `--api-key` flag or `NOVITA_API_KEY` env var is required for all commands
- Use `novita files upload` to upload JSONL for batch processing, then `novita batch create <file_id>`

## Verified Endpoints (E2E Tested)

| Endpoint | CLI Command | Test Status |
|----------|-------------|-------------|
| POST /v3/openai/chat/completions | `novita chat` | Passed (streaming + JSON + system) |
| POST /v3/openai/completions | `novita complete` | Passed (text + JSON) |
| POST /v3/openai/embeddings | `novita embed` | Passed (1024-dim verified) |
| POST /v3/openai/rerank | `novita rerank` | Passed (ranking + scores) |
| GET /v3/openai/models | `novita models list/get` | Passed (list + get by ID) |
| POST /v3beta/flux-1-schnell | `novita image flux` | Passed (download to disk) |
| POST /v3/async/txt2img | `novita image generate` | Passed (full async lifecycle) |
| POST /v3/async/img2img | `novita image img2img` | Passed |
| POST /v3/async/inpainting | `novita image inpainting` | Passed |
| POST /v3/async/upscale | `novita image upscale` | Passed (FLUX -> upscale -> poll) |
| POST /v3/remove-background | `novita image remove-bg` | Passed (FLUX -> remove-bg pipeline) |
| POST /v3/async/replace-background | `novita image replace-bg` | Passed |
| POST /v3/reimagine | `novita image reimagine` | Passed |
| POST /v3/cleanup | `novita image cleanup` | Passed |
| POST /v3/outpainting | `novita image outpainting` | Passed |
| POST /v3/remove-text | `novita image remove-text` | Passed |
| POST /v3/img2prompt | `novita image to-prompt` | Passed |
| POST /v3/merge-face | `novita image merge-face` | Passed |
| POST /v3/async/txt2video | `novita video generate` | Passed (submit + status check) |
| POST /v3/async/hunyuan-video-fast | `novita video hunyuan` | Passed (submit + status check) |
| POST /v3/minimax-speech-02-hd | `novita audio tts` | Passed (download + ASR round-trip) |
| POST /v3/glm-tts | `novita audio glm-tts` | Passed |
| POST /v3/glm-asr | `novita audio asr` | Passed (base64 data URI, round-trip) |
| POST /v3/minimax-voice-cloning | `novita audio voice-clone` | Passed |
| GET /v3/user | `novita account balance` | Passed |
| GET (billing) | `novita account billing` | Passed |
| GET (usage-billing) | `novita account usage-billing` | Passed |
| GET (fixed-billing) | `novita account fixed-billing` | Passed |
| GET /openai/v1/files | `novita files list` | Passed |
| POST /openai/v1/files | `novita files upload` | Passed |
| GET /openai/v1/files/{id} | `novita files get` | Passed |
| DELETE /openai/v1/files/{id} | `novita files delete` | Passed |
| GET /openai/v1/files/{id}/content | `novita files content` | Passed |
| POST /openai/v1/batches | `novita batch create` | Passed (full lifecycle) |
| GET /openai/v1/batches | `novita batch list/get` | Passed |
| POST .../gpu/instance/create+delete | `novita gpu create/delete` | Passed (full lifecycle) |
| POST .../gpu/instance/restart | `novita gpu restart` | Passed |
| GET .../gpu/instances | `novita gpu list` | Passed |
| GET .../gpu/instance | `novita gpu get` | Passed |
| GET .../products | `novita gpu products` | Passed |
| GET .../cpu/products | `novita gpu cpu-products` | Passed |
| GET .../clusters | `novita gpu clusters` | Passed |
| GET .../networkstorages | `novita storage list` | Passed |
| POST .../networkstorage/create | `novita storage create` | Passed |
| POST .../template/create+delete | `novita template create/delete` | Passed (full lifecycle) |
| POST .../template/update | `novita template edit` | Passed |
| GET .../template | `novita template get` | Passed |
| GET .../templates | `novita template list` | Passed |
| GET .../endpoints | `novita serverless list` | Passed |
| GET /v3/async/task-result | `novita task status/wait` | Passed (full async lifecycle) |
