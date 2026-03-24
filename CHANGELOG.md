# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-24

### Added

#### Image Editing (9 new commands)
- `novita image img2img` - Image-to-image generation with prompt guidance (async)
- `novita image inpainting` - Inpaint masked regions of an image (async)
- `novita image replace-bg` - Replace image background with AI-generated scene (async)
- `novita image reimagine` - Reimagine/restyle an image (sync)
- `novita image cleanup` - Erase/clean up masked region of an image (sync)
- `novita image outpainting` - Extend image beyond its borders (sync)
- `novita image remove-text` - Remove text from an image (sync)
- `novita image to-prompt` - Generate a text description from an image (sync)
- `novita image merge-face` - Merge a face onto another image (sync)

#### Files API (5 new commands)
- `novita files upload` - Upload JSONL files for batch processing
- `novita files list` - List uploaded files
- `novita files get` - Get file details
- `novita files delete` - Delete an uploaded file
- `novita files content` - Retrieve file content

#### Audio (2 new commands)
- `novita audio glm-tts` - GLM text-to-speech with 7 voice options (binary PCM/WAV output)
- `novita audio voice-clone` - Clone a voice from audio via MiniMax

#### Billing (2 new commands)
- `novita account usage-billing` - Query usage-based billing details
- `novita account fixed-billing` - Query fixed-term billing details

#### GPU & Infrastructure (6 new commands)
- `novita gpu restart` - Restart a GPU instance
- `novita gpu clusters` - List available data center clusters
- `novita storage list` - List network storage volumes
- `novita storage create` - Create a network storage volume
- `novita storage delete` - Delete a network storage volume
- `novita template edit` - Edit an existing GPU template

### Changed
- Version bumped to 0.2.0
- Repository URL updated to `github.com/jaxzhang-novita/cnovita`

### Tests
- Unit tests: 34 passed (was 32)
- E2E tests: 61 passed (was 45), all real API calls, zero mocks
- Total: 95 passed, 100% pass rate
- New E2E test coverage for: files lifecycle, image editing (to-prompt, reimagine, remove-text), billing APIs, GPU clusters, storage listing, template edit lifecycle, GLM TTS

## [0.1.0] - 2026-03-24

### Added
- Initial release of cnovita CLI
- LLM APIs: `chat`, `complete`, `embed`, `rerank`, `models list/get`
- Image generation: `image generate` (SD txt2img), `image flux` (FLUX.1 Schnell), `image upscale`, `image remove-bg`
- Video generation: `video generate` (txt2video), `video from-image` (img2video), `video hunyuan`
- Audio: `audio tts` (MiniMax Speech-02-HD), `audio asr` (GLM ASR)
- Account: `account balance`, `account billing`
- Task management: `task status`, `task wait`
- Batch processing: `batch create`, `batch list`, `batch get`, `batch cancel`
- GPU instances: `gpu list`, `gpu create`, `gpu get`, `gpu start`, `gpu stop`, `gpu delete`, `gpu products`, `gpu cpu-products`, `gpu metrics`, `gpu edit`
- GPU templates: `template list`, `template get`, `template create`, `template delete`
- Serverless endpoints: `serverless list`, `serverless get`, `serverless create`, `serverless update`, `serverless delete`
- Global options: `--api-key`, `--json-output`
- 77 tests (32 unit + 45 E2E), 100% pass rate
