# Novita AI CLI - Test Plan & Results

## Test Plan

### Unit Tests (test_core.py) - 32 tests
- **NovitaClient**: Init with key, init from env, missing key raises error
- **NovitaError**: Error attributes (message, status_code, error_code)
- **Output Utils**: format_balance, format_table (empty + data)
- **CLI Help**: All 15 command groups emit correct help text and subcommands
- **CLI Mocked**: 7 commands with JSON rendering (fast, no API)
- **CLI Subprocess**: Entry points resolve and produce help

### E2E Tests (test_full_e2e.py) - 45 tests, ALL real API calls
Every test hits the live Novita AI API. Zero mocks, zero fakes.

| API | Tests | Lifecycle / Coverage |
|-----|-------|---------------------|
| **Chat** | 3 | Streaming, no-stream JSON, system prompt |
| **Complete** | 2 | Text, JSON |
| **Embed** | 2 | 1024-dim text, JSON |
| **Rerank** | 2 | Text ranking, JSON with scores |
| **Models** | 3 | List table, list JSON, **get by ID** |
| **FLUX Image** | 2 | JSON, download to disk |
| **Async txt2img** | 1 | **generate --no-wait -> task status -> task wait -> download** |
| **Image Upscale** | 1 | **FLUX -> download -> upscale --no-wait -> poll -> verify** |
| **Image Remove-BG** | 1 | **FLUX -> download -> remove-bg -> verify output** |
| **Video txt2video** | 1 | **Submit -> verify task_id -> check status** |
| **Video Hunyuan** | 1 | **Submit -> verify task_id -> check status** |
| **TTS Audio** | 2 | JSON, download MP3 |
| **ASR Audio** | 1 | **TTS -> download -> ASR -> verify transcript** |
| **Account** | 4 | Balance text/JSON, billing text/JSON |
| **Batch** | 3 | List text/JSON, **upload file -> create -> get -> list -> cancel** |
| **GPU Products** | 5 | Products table/JSON, instances list/JSON, CPU products |
| **GPU Instance** | 1 | **CREATE -> GET -> LIST -> DELETE (spot, multi-product)** |
| **Template** | 2 | **CREATE -> GET -> LIST -> CLI GET -> DELETE -> verify gone** |
| **Serverless** | 2 | List text/JSON |
| **Task API** | 1 | **Submit -> status text -> status JSON -> poll -> complete** |
| **Subprocess** | 5 | Chat, models, embed, GPU products, balance |

## Resource Lifecycles (8 total)

| Resource | Lifecycle Steps | Test |
|----------|----------------|------|
| **GPU Instance** | CREATE (spot) -> GET -> LIST -> DELETE -> verify removed | test_gpu_instance_create_get_delete |
| **Template** | CREATE -> GET -> LIST -> CLI GET -> DELETE -> verify gone | test_template_full_lifecycle |
| **Batch** | Upload JSONL -> CREATE -> GET -> LIST -> cancel | test_batch_full_lifecycle |
| **Async Image** | CLI generate --no-wait -> CLI task status -> CLI task wait -> download file | test_image_generate_nowait_then_task_wait |
| **Image Upscale** | FLUX generate -> download -> upscale --no-wait -> poll -> verify URL | test_flux_then_upscale |
| **Image Remove-BG** | FLUX generate -> download -> CLI remove-bg -> verify output file | test_flux_then_remove_bg |
| **Audio Round-Trip** | TTS -> download MP3 -> CLI ASR -> verify "hello","world","speech" | test_tts_then_asr_roundtrip |
| **Task API** | Client submit txt2img -> CLI status -> CLI status JSON -> client poll -> verify SUCCEED | test_task_lifecycle_submit_status_wait |

## Test Results

```
======================== 77 passed in 212.89s (0:03:32) ========================
```

**Total: 77/77 tests passed (100%)**
- 32 unit tests
- 45 E2E tests (all real API, zero mocks)
- 8 resource lifecycle tests
- 0 failures
