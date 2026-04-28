# Verified Endpoint Coverage

This skill wraps the current `novita` CLI, which calls Novita API endpoints through `novita_cli.core.client.NovitaClient`.

## OpenAI-Compatible APIs

| Capability | Client method |
|------------|---------------|
| Chat completion | `chat_completion` |
| Text completion | `completion` |
| Embeddings | `embeddings` |
| Rerank | `rerank` |
| List models | `list_models` |
| Retrieve model | `retrieve_model` |

## Image APIs

| Capability | Client method | Sync |
|------------|---------------|------|
| Stable Diffusion text-to-image | `txt2img` | Async |
| FLUX.1 Schnell | `flux_schnell` | Sync |
| Image-to-image | `img2img` | Async |
| Upscale | `upscale` | Async |
| Remove background | `remove_background` | Sync |
| Replace background | `replace_background` | Async |
| Inpainting | `inpainting` | Async |
| Reimagine | `reimagine` | Sync |
| Image to prompt | `img2prompt` | Sync |
| Merge face | `merge_face` | Sync |
| Cleanup | `cleanup` | Sync |
| Outpainting | `outpainting` | Sync |
| Remove text | `remove_text` | Sync |

## Video And Audio APIs

| Capability | Client method |
|------------|---------------|
| Text-to-video | `txt2video` |
| Image-to-video | `img2video` |
| Hunyuan video | `hunyuan_video` |
| MiniMax TTS | `minimax_tts` |
| GLM TTS | `glm_tts` |
| ASR | `speech_to_text` |
| Voice clone | `voice_clone` |

## Management APIs

The CLI also covers account billing, async tasks, batch/files, GPU instances, templates, network storage, and serverless endpoints.
