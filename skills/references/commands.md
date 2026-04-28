# Novita CLI Command Reference

Read this file when you need a concise command map. Use `novita --help` or command-specific `--help` for exact local options.

## LLM

```bash
novita chat "Hello" -m deepseek/deepseek-v3-0324
novita chat "Hello" --no-stream --json-output
novita complete "Once upon a time"
novita embed "text" -m baai/bge-m3
novita rerank "query" -d "doc1" -d "doc2"
novita models list
novita models get <model_id>
```

## Images

```bash
novita image flux "a sunset" -W 512 -H 512 -o ./outputs
novita image generate "a cat" -W 1024 -H 1024 --steps 20 -o ./outputs
novita image img2img input.png "watercolor style"
novita image inpainting input.png mask.png "add a red flower"
novita image upscale input.png --scale 2
novita image remove-bg input.png -o clean.png
novita image replace-bg input.png "beach sunset" -o ./outputs
novita image reimagine input.png -o reimagined.png
novita image cleanup input.png mask.png -o cleaned.png
novita image outpainting input.png "extend into a forest" -W 1536 -H 1024
novita image remove-text input.png -o no-text.png
novita image to-prompt input.png
novita image merge-face face.png target.png -o merged.png
```

## Video

```bash
novita video generate "snow scene" --frames 32
novita video from-image image.png --model SVD-XT
novita video hunyuan "a cat playing piano"
```

## Audio

```bash
novita audio tts "Hello world" --voice Calm_Woman -o hello.mp3
novita audio glm-tts "你好" --voice jam -o hello.wav
novita audio asr recording.wav
novita audio voice-clone https://example.com/voice.mp3
```

## Account, Tasks, Files, And Infrastructure

```bash
novita account balance
novita account billing
novita task status <task_id>
novita task wait <task_id> -o ./outputs --timeout 600
novita files upload batch.jsonl
novita batch create <file_id>
novita gpu products
novita gpu list
novita template list
novita storage list
novita serverless list
```

