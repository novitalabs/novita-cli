# NOVITA.md - Novita AI CLI SOP

## Architecture

Novita AI provides a unified API platform with:
- **LLM APIs** (OpenAI-compatible): Chat, completion, embeddings, rerank at `api.novita.ai/v3/openai/`
- **Async Media APIs**: Image generation (txt2img, img2img, upscale), video (txt2video, img2video, hunyuan), audio (TTS, ASR) - return task_id, poll with task-result
- **Sync Media APIs**: FLUX.1 Schnell (images), remove-background, GLM ASR
- **Account APIs**: Balance, billing at `/v3/user/`
- **Batch APIs**: Bulk LLM inference via OpenAI-compatible batch endpoints

## API Patterns

1. **Auth**: Bearer token in Authorization header
2. **Sync endpoints**: POST/GET, return result directly
3. **Async endpoints**: POST returns `{task_id}`, poll `GET /v3/async/task-result?task_id=X`
4. **Task statuses**: TASK_STATUS_QUEUED -> TASK_STATUS_PROCESSING -> TASK_STATUS_SUCCEED / TASK_STATUS_FAILED
5. **Streaming**: SSE format for chat/completion, `data: [DONE]` terminator

## CLI Mapping

| API Endpoint | CLI Command |
|---|---|
| POST /v3/openai/chat/completions | `novita chat` |
| POST /v3/openai/completions | `novita complete` |
| POST /v3/openai/embeddings | `novita embed` |
| POST /v3/openai/rerank | `novita rerank` |
| GET /v3/openai/models | `novita models list` |
| POST /v3/async/txt2img | `novita image generate` |
| POST /v3beta/flux-1-schnell | `novita image flux` |
| POST /v3/async/upscale | `novita image upscale` |
| POST /v3/remove-background | `novita image remove-bg` |
| POST /v3/async/txt2video | `novita video generate` |
| POST /v3/async/img2video | `novita video from-image` |
| POST /v3/async/hunyuan-video-fast | `novita video hunyuan` |
| POST /v3/minimax-speech-02-hd | `novita audio tts` |
| POST /v3/glm-asr | `novita audio asr` |
| GET /v3/user | `novita account balance` |
| GET /v3/async/task-result | `novita task status/wait` |
| POST /v3/openai/batches | `novita batch create/list/get/cancel` |
| GET /gpu-instance/openapi/v1/products | `novita gpu products` |
| GET /gpu-instance/openapi/v1/gpu/instances | `novita gpu list` |
| POST /gpu-instance/openapi/v1/gpu/instance/create | `novita gpu create` |
| GET /gpu-instance/openapi/v1/gpu/instance | `novita gpu get` |
| POST .../instance/start\|stop\|delete | `novita gpu start/stop/delete` |
| POST .../instance/edit | `novita gpu edit` |
| GET /openapi/v1/metrics/gpu/instance | `novita gpu metrics` |
| GET /gpu-instance/openapi/v1/templates | `novita template list` |
| POST .../template/create\|update\|delete | `novita template create/delete` |
| GET /gpu-instance/openapi/v1/endpoints | `novita serverless list` |
| POST .../endpoint/create\|update\|delete | `novita serverless create/update/delete` |
