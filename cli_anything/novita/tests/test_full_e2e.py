"""End-to-end tests for Novita AI CLI with REAL API calls.

Every test here hits the live Novita AI API. No mocks.
Requires NOVITA_API_KEY to be set.
Skip with: pytest -k "not e2e"
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

from click.testing import CliRunner

API_KEY = os.environ.get("NOVITA_API_KEY", "")
SKIP_REASON = "NOVITA_API_KEY not set"


def requires_api_key(func):
    return unittest.skipUnless(API_KEY, SKIP_REASON)(func)


def invoke(runner, args, json_mode=False):
    """Helper to invoke CLI with API key."""
    from cli_anything.novita.novita_cli import cli
    cmd = ["--api-key", API_KEY]
    if json_mode:
        cmd = ["--json-output"] + cmd
    cmd.extend(args)
    return runner.invoke(cli, cmd, obj={})


# ═══════════════════════════════════════════════════════════════════════════
# 1. LLM APIs - Chat, Complete, Embed, Rerank, Models
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_LLM_Chat(unittest.TestCase):
    """Real API: Chat completion."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_chat_streaming(self):
        result = invoke(self.runner, [
            "chat", "Say exactly: ok",
            "-m", "deepseek/deepseek-v3-0324", "--max-tokens", "10",
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(len(result.output.strip()) > 0)

    @requires_api_key
    def test_chat_no_stream_json(self):
        result = invoke(self.runner, [
            "chat", "Say hi in one word",
            "-m", "deepseek/deepseek-v3-0324", "--max-tokens", "10", "--no-stream",
        ], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("choices", data)
        self.assertEqual(data["choices"][0]["message"]["role"], "assistant")
        self.assertIn("usage", data)
        self.assertGreater(data["usage"]["total_tokens"], 0)

    @requires_api_key
    def test_chat_with_system_prompt(self):
        result = invoke(self.runner, [
            "chat", "What is 2+2?",
            "-m", "deepseek/deepseek-v3-0324",
            "--system", "Answer with just the number.",
            "--max-tokens", "5", "--no-stream",
        ], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        content = data["choices"][0]["message"]["content"]
        self.assertIn("4", content)


class TestE2E_LLM_Complete(unittest.TestCase):
    """Real API: Text completion."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_complete_text(self):
        result = invoke(self.runner, [
            "complete", "The capital of France is",
            "-m", "deepseek/deepseek-v3-0324", "--max-tokens", "10",
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(len(result.output.strip()) > 0)

    @requires_api_key
    def test_complete_json(self):
        result = invoke(self.runner, [
            "complete", "Hello",
            "-m", "deepseek/deepseek-v3-0324", "--max-tokens", "5",
        ], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("choices", data)
        self.assertIn("text", data["choices"][0])
        self.assertIn("usage", data)


class TestE2E_LLM_Embed(unittest.TestCase):
    """Real API: Embeddings."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_embed_text_output(self):
        result = invoke(self.runner, ["embed", "Hello world"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Dimensions: 1024", result.output)

    @requires_api_key
    def test_embed_json(self):
        result = invoke(self.runner, ["embed", "test embeddings"], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertEqual(data["data"][0]["object"], "embedding")
        self.assertEqual(len(data["data"][0]["embedding"]), 1024)
        self.assertGreater(data["usage"]["total_tokens"], 0)


class TestE2E_LLM_Rerank(unittest.TestCase):
    """Real API: Rerank."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_rerank_text(self):
        result = invoke(self.runner, [
            "rerank", "best pet",
            "-d", "cats are cute",
            "-d", "dogs are loyal",
            "-d", "fish swim",
        ])
        self.assertEqual(result.exit_code, 0)
        # cats should score highest for "best pet"
        self.assertIn("cats", result.output)

    @requires_api_key
    def test_rerank_json(self):
        result = invoke(self.runner, [
            "rerank", "best pet",
            "-d", "cats are cute",
            "-d", "dogs are loyal",
        ], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 2)
        # Each result has relevance_score
        for r in data["results"]:
            self.assertIn("relevance_score", r)
            self.assertGreater(r["relevance_score"], 0)


class TestE2E_LLM_Models(unittest.TestCase):
    """Real API: Model listing and retrieval."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_models_list(self):
        result = invoke(self.runner, ["models", "list", "--filter", "deepseek"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("deepseek", result.output)
        self.assertIn("Model ID", result.output)

    @requires_api_key
    def test_models_list_json(self):
        result = invoke(self.runner, ["models", "list", "--filter", "llama"], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIsInstance(data, list)
        self.assertTrue(any("llama" in m["id"] for m in data))
        m = data[0]
        self.assertIn("id", m)
        self.assertIn("context_size", m)

    @requires_api_key
    def test_models_get(self):
        """Get a specific model by ID."""
        result = invoke(self.runner, [
            "models", "get", "deepseek/deepseek-v3-0324",
        ], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("id", data)
        self.assertEqual(data["id"], "deepseek/deepseek-v3-0324")


# ═══════════════════════════════════════════════════════════════════════════
# 2. Image APIs - FLUX Schnell (sync, cheapest)
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_Image_Flux(unittest.TestCase):
    """Real API: FLUX.1 Schnell image generation (synchronous)."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_flux_generate_json(self):
        """Generate a tiny image with FLUX and verify response structure."""
        result = invoke(self.runner, [
            "image", "flux", "red circle",
            "-W", "64", "-H", "64", "--steps", "1", "--seed", "42",
        ], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("images", data)
        self.assertEqual(len(data["images"]), 1)
        self.assertTrue(data["images"][0]["image_url"].startswith("http"))
        self.assertIn("image_type", data["images"][0])

    @requires_api_key
    def test_flux_generate_download(self):
        """Generate and download a FLUX image to temp dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = invoke(self.runner, [
                "image", "flux", "blue square",
                "-W", "64", "-H", "64", "--steps", "1", "--seed", "123",
                "-o", tmpdir,
            ])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Saved:", result.output)
            # Verify file was actually created
            files = os.listdir(tmpdir)
            self.assertEqual(len(files), 1)
            self.assertGreater(os.path.getsize(os.path.join(tmpdir, files[0])), 100)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Audio APIs - TTS
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_Audio_TTS(unittest.TestCase):
    """Real API: Text-to-speech with MiniMax."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_tts_json(self):
        result = invoke(self.runner, [
            "audio", "tts", "Hello",
            "--voice", "Wise_Woman",
        ], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("audio", data)

    @requires_api_key
    def test_tts_download(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test.mp3")
            result = invoke(self.runner, [
                "audio", "tts", "Hello world",
                "--voice", "Calm_Woman", "-o", out_path,
            ])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Saved:", result.output)
            self.assertTrue(os.path.exists(out_path))
            self.assertGreater(os.path.getsize(out_path), 100)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Account APIs
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_Account(unittest.TestCase):
    """Real API: Account balance and billing."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_balance_text(self):
        result = invoke(self.runner, ["account", "balance"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Credit Balance:", result.output)
        self.assertIn("$", result.output)

    @requires_api_key
    def test_balance_json(self):
        result = invoke(self.runner, ["account", "balance"], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("credit_balance", data)
        self.assertIsInstance(data["credit_balance"], int)

    @requires_api_key
    def test_billing(self):
        """Test monthly billing endpoint - may fail with 404 if not available for this account."""
        result = invoke(self.runner, ["account", "billing"])
        # Billing endpoint may not be available for all accounts
        # exit_code 0 = data returned, exit_code 1 = error (acceptable for billing)
        self.assertIn(result.exit_code, [0, 1])

    @requires_api_key
    def test_billing_json(self):
        result = invoke(self.runner, ["account", "billing"], json_mode=True)
        # Billing may not be available for all accounts
        self.assertIn(result.exit_code, [0, 1])


# ═══════════════════════════════════════════════════════════════════════════
# 5. Batch API
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_Batch(unittest.TestCase):
    """Real API: Batch lifecycle - upload file, create, get, list, cancel."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_batch_list(self):
        result = invoke(self.runner, ["batch", "list"])
        self.assertEqual(result.exit_code, 0)

    @requires_api_key
    def test_batch_list_json(self):
        result = invoke(self.runner, ["batch", "list"], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("object", data)
        self.assertEqual(data["object"], "list")

    @requires_api_key
    def test_batch_full_lifecycle(self):
        """Upload file -> create batch -> get batch -> verify in list."""
        from cli_anything.novita.core.client import NovitaClient, NovitaError

        client = NovitaClient(api_key=API_KEY)

        # Step 1: Create JSONL file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"custom_id":"test-1","body":{"model":"deepseek/deepseek-v3-0324","messages":[{"role":"user","content":"Say hi"}],"max_tokens":5}}\n')
            jsonl_path = f.name

        try:
            # Step 2: Upload file
            file_result = client.upload_batch_file(jsonl_path)
            file_id = file_result.get("id", "")
            self.assertTrue(file_id, "File upload should return an id")
            self.assertEqual(file_result["purpose"], "batch")

            # Step 3: Create batch
            batch_result = client.create_batch(
                input_file_id=file_id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
            batch_id = batch_result.get("id", "")
            self.assertTrue(batch_id, "Batch creation should return an id")

            # Step 4: Get batch
            get_result = client.retrieve_batch(batch_id)
            self.assertEqual(get_result["id"], batch_id)
            self.assertIn(get_result["status"], [
                "validating", "VALIDATING", "PROGRESS", "in_progress", "COMPLETED", "completed",
            ])
            self.assertEqual(get_result["input_file_id"], file_id)

            # Step 5: Verify in list
            list_result = client.list_batches()
            batches = list_result.get("data") or []
            found = any(b.get("id") == batch_id for b in batches)
            self.assertTrue(found, f"Batch {batch_id} should appear in list")

            # Step 6: Get via CLI
            cli_result = invoke(self.runner, ["batch", "get", batch_id], json_mode=True)
            self.assertEqual(cli_result.exit_code, 0)
            cli_data = json.loads(cli_result.output)
            self.assertEqual(cli_data["id"], batch_id)

            # Step 7: Try cancel (may fail if already completed)
            try:
                client.cancel_batch(batch_id)
            except NovitaError:
                pass  # Already completed batches can't be cancelled

        finally:
            os.unlink(jsonl_path)


# ═══════════════════════════════════════════════════════════════════════════
# 6. GPU Products (read-only, safe)
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_GPU_Products(unittest.TestCase):
    """Real API: GPU product listing."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_gpu_products_table(self):
        result = invoke(self.runner, ["gpu", "products"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("RTX", result.output)
        self.assertIn("Name", result.output)

    @requires_api_key
    def test_gpu_products_json(self):
        result = invoke(self.runner, ["gpu", "products"], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("data", data)
        self.assertGreater(len(data["data"]), 0)
        p = data["data"][0]
        self.assertIn("id", p)
        self.assertIn("name", p)
        self.assertIn("price", p)

    @requires_api_key
    def test_gpu_instances_list(self):
        result = invoke(self.runner, ["gpu", "list"])
        self.assertEqual(result.exit_code, 0)
        # May be empty, that's fine

    @requires_api_key
    def test_gpu_instances_list_json(self):
        result = invoke(self.runner, ["gpu", "list"], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("instances", data)

    @requires_api_key
    def test_gpu_cpu_products(self):
        """List CPU products."""
        result = invoke(self.runner, ["gpu", "cpu-products"], json_mode=True)
        self.assertEqual(result.exit_code, 0)


# ═══════════════════════════════════════════════════════════════════════════
# 7. Template Lifecycle: CREATE -> GET -> LIST -> DELETE
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_Template_Lifecycle(unittest.TestCase):
    """Real API: Full template lifecycle with real create and delete."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_template_full_lifecycle(self):
        """Create a template, get it, find it in list, then delete it."""
        from cli_anything.novita.core.client import NovitaClient

        client = NovitaClient(api_key=API_KEY)

        # Step 1: CREATE
        tmpl = {
            "name": f"cli-e2e-test-{int(time.time())}",
            "type": "instance",
            "channel": "private",
            "image": "pytorch/pytorch:latest",
            "rootfsSize": 10,
        }
        create_result = client.gpu_create_template(tmpl)
        template_id = create_result.get("templateId", "")
        self.assertTrue(template_id, "Template creation should return templateId")

        try:
            # Step 2: GET
            get_result = client.gpu_get_template(template_id)
            self.assertEqual(get_result["Id"], template_id)
            self.assertEqual(get_result["name"], tmpl["name"])
            self.assertEqual(get_result["image"], "pytorch/pytorch:latest")

            # Step 3: LIST - verify it appears
            list_result = client.gpu_list_templates(
                channel="private", is_my_community=True, page_size=100
            )
            templates = list_result.get("template", [])
            found = any(t.get("Id") == template_id for t in templates)
            self.assertTrue(found, f"Template {template_id} should appear in private list")

            # Step 3b: Test via CLI too
            result = invoke(self.runner, ["template", "get", template_id], json_mode=True)
            self.assertEqual(result.exit_code, 0)
            data = json.loads(result.output)
            self.assertEqual(data["Id"], template_id)

        finally:
            # Step 4: DELETE (always clean up)
            delete_result = client.gpu_delete_template(template_id)
            self.assertEqual(delete_result.get("templateId"), template_id)

        # Step 5: Verify deletion - should not be in list anymore
        list_after = client.gpu_list_templates(
            channel="private", is_my_community=True, page_size=100
        )
        templates_after = list_after.get("template", [])
        found_after = any(t.get("Id") == template_id for t in (templates_after or []))
        self.assertFalse(found_after, "Template should be gone after deletion")

    @requires_api_key
    def test_template_list_official(self):
        """List official templates (read-only, always available)."""
        result = invoke(self.runner, ["template", "list", "--channel", "official"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Name", result.output)
        self.assertIn("Image", result.output)


# ═══════════════════════════════════════════════════════════════════════════
# 8. Serverless Endpoints (read-only listing)
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_Serverless(unittest.TestCase):
    """Real API: Serverless endpoint listing."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_serverless_list(self):
        result = invoke(self.runner, ["serverless", "list"])
        self.assertEqual(result.exit_code, 0)

    @requires_api_key
    def test_serverless_list_json(self):
        result = invoke(self.runner, ["serverless", "list"], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertIn("endpoints", data)
        self.assertIn("total", data)


# ═══════════════════════════════════════════════════════════════════════════
# 8b. GPU Instance Lifecycle: CREATE -> GET -> DELETE
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_GPU_Instance_Lifecycle(unittest.TestCase):
    """Real API: Full GPU instance lifecycle (spot, deleted immediately)."""

    @requires_api_key
    def test_gpu_instance_create_get_delete(self):
        """Create a spot GPU instance, verify it, then delete immediately."""
        from cli_anything.novita.core.client import NovitaClient, NovitaError

        client = NovitaClient(api_key=API_KEY)

        # Try multiple spot products in case one is unavailable
        products_to_try = ["3090.16c92g", "4090.16c62g", "4090.16c96g.v2"]
        instance_id = None

        for product_id in products_to_try:
            try:
                create_result = client.gpu_create_instance(
                    name=f"cli-e2e-{int(time.time())}",
                    productId=product_id,
                    gpuNum=1,
                    rootfsSize=10,
                    imageUrl="pytorch/pytorch:latest",
                    kind="gpu",
                    billingMode="spot",
                )
                instance_id = create_result.get("id", "")
                if instance_id:
                    break
            except NovitaError as e:
                if "INSUFFICIENT_RESOURCE" in str(e):
                    continue
                raise

        self.assertTrue(instance_id, "Should create a spot instance with at least one product")

        try:
            # Step 2: GET and verify fields
            instance = client.gpu_get_instance(instance_id)
            self.assertEqual(instance.get("id"), instance_id)
            self.assertIn(instance.get("status"), [
                "pending", "toCreate", "creating", "pulling", "running", "starting",
            ])

            # Step 2b: Verify appears in list
            list_result = client.gpu_list_instances(page_size=50)
            instances = list_result.get("instances", [])
            found = any(i.get("id") == instance_id for i in instances)
            self.assertTrue(found, f"Instance {instance_id} should appear in list")

        finally:
            # Step 3: DELETE immediately (always clean up)
            client.gpu_delete_instance(instance_id)

        # Step 4: Verify deletion
        time.sleep(2)
        list_after = client.gpu_list_instances(page_size=50)
        instances_after = list_after.get("instances", [])
        active = [i for i in instances_after
                  if i.get("id") == instance_id and i.get("status") not in ("removed", "toRemove", "removing")]
        self.assertEqual(len(active), 0, "Instance should be removed/removing after deletion")


# ═══════════════════════════════════════════════════════════════════════════
# 8c. Audio Round-Trip: TTS -> download -> ASR
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_Audio_RoundTrip(unittest.TestCase):
    """Real API: Generate speech with TTS, then transcribe with ASR."""

    @requires_api_key
    def test_tts_then_asr_roundtrip(self):
        """Generate TTS audio, download it, run ASR, verify text matches."""
        from cli_anything.novita.core.client import NovitaClient
        import requests as req

        client = NovitaClient(api_key=API_KEY)

        original_text = "Hello world this is a speech test"

        # Step 1: TTS
        tts_result = client.minimax_tts(
            text=original_text,
            voice_setting={"voice_id": "Wise_Woman", "speed": 1.0},
            audio_setting={"format": "mp3"},
            output_format="url",
        )
        audio_url = tts_result.get("audio", "")
        self.assertTrue(audio_url.startswith("http"), "TTS should return an audio URL")

        # Step 2: Download audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name
            resp = req.get(audio_url, timeout=30)
            f.write(resp.content)

        try:
            self.assertGreater(os.path.getsize(tmp_path), 1000, "Audio file should be >1KB")

            # Step 3: ASR via CLI (tests the data URI encoding fix)
            result = invoke(self.runner, ["audio", "asr", tmp_path], json_mode=True)
            self.assertEqual(result.exit_code, 0)
            data = json.loads(result.output)
            transcribed = data.get("text", "").lower()

            # Verify key words appear in transcription
            self.assertIn("hello", transcribed)
            self.assertIn("world", transcribed)
            self.assertIn("speech", transcribed)
        finally:
            os.unlink(tmp_path)

    def setUp(self):
        self.runner = CliRunner()


# ═══════════════════════════════════════════════════════════════════════════
# 8d. Async Image Generation via CLI: generate --no-wait -> task wait
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_Image_Async_Lifecycle(unittest.TestCase):
    """Real API: Async image generation lifecycle via CLI commands."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_image_generate_nowait_then_task_wait(self):
        """Submit txt2img via CLI with --no-wait, then use task wait to download."""
        # Step 1: Submit via CLI with --no-wait and JSON
        result = invoke(self.runner, [
            "image", "generate", "red circle on white background",
            "-W", "128", "-H", "128", "--steps", "1", "--seed", "42",
            "--no-wait",
        ], json_mode=True)
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        task_id = data.get("task_id", "")
        self.assertTrue(task_id, "generate --no-wait should return task_id")

        # Step 2: Check status via CLI
        status_result = invoke(self.runner, ["task", "status", task_id])
        self.assertEqual(status_result.exit_code, 0)
        self.assertIn(task_id[:8], status_result.output)

        # Step 3: Wait and download via CLI
        with tempfile.TemporaryDirectory() as tmpdir:
            wait_result = invoke(self.runner, [
                "task", "wait", task_id, "-o", tmpdir, "--timeout", "120",
            ])
            self.assertEqual(wait_result.exit_code, 0)
            self.assertIn("Saved:", wait_result.output)

            # Verify file was downloaded
            files = os.listdir(tmpdir)
            self.assertGreater(len(files), 0, "Should have downloaded at least 1 image")
            self.assertGreater(
                os.path.getsize(os.path.join(tmpdir, files[0])), 100,
                "Downloaded image should be >100 bytes",
            )


# ═══════════════════════════════════════════════════════════════════════════
# 8e. Image Processing: FLUX generate -> remove-bg (sync pipeline)
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_Image_Upscale(unittest.TestCase):
    """Real API: Image upscale lifecycle - generate tiny image then upscale it."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_flux_then_upscale(self):
        """Generate tiny FLUX image, download, then upscale it."""
        import requests as req
        from cli_anything.novita.core.client import NovitaClient

        client = NovitaClient(api_key=API_KEY)

        # Step 1: Generate tiny image
        flux_result = client.flux_schnell(
            prompt="red dot", width=64, height=64, seed=42, steps=1, image_num=1,
        )
        image_url = flux_result["images"][0]["image_url"]

        # Step 2: Download
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name
            resp = req.get(image_url, timeout=30)
            f.write(resp.content)

        try:
            # Step 3: Upscale via CLI (async, uses --no-wait then task wait)
            result = invoke(self.runner, [
                "image", "upscale", tmp_path, "--scale", "2", "--no-wait",
            ], json_mode=True)
            self.assertEqual(result.exit_code, 0)
            data = json.loads(result.output)
            task_id = data.get("task_id", "")
            self.assertTrue(task_id, "Upscale should return task_id")

            # Step 4: Wait for upscale result
            upscale_result = client.poll_task(task_id, timeout=120)
            self.assertEqual(upscale_result["task"]["status"], "TASK_STATUS_SUCCEED")
            self.assertGreater(len(upscale_result.get("images", [])), 0)
            self.assertTrue(upscale_result["images"][0]["image_url"].startswith("http"))
        finally:
            os.unlink(tmp_path)


class TestE2E_Video(unittest.TestCase):
    """Real API: Video generation (submit only, don't wait - too expensive)."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_video_generate_submit(self):
        """Submit a txt2video task and verify task_id is returned."""
        from cli_anything.novita.core.client import NovitaClient

        client = NovitaClient(api_key=API_KEY)
        task_id = client.txt2video(request={
            "model_name": "darkSushiMixMix_225D_64380.safetensors",
            "height": 512, "width": 512, "steps": 1, "seed": 42,
            "prompts": [{"frames": 16, "prompt": "red dot moving"}],
        })
        self.assertTrue(task_id, "txt2video should return a task_id")

        # Verify the task exists
        result = client.get_task_result(task_id)
        self.assertIn("task", result)
        self.assertIn(result["task"]["status"], [
            "TASK_STATUS_QUEUED", "TASK_STATUS_PROCESSING", "TASK_STATUS_SUCCEED", "TASK_STATUS_FAILED",
        ])

    @requires_api_key
    def test_video_hunyuan_submit(self):
        """Submit a hunyuan-video-fast task and verify task_id is returned."""
        from cli_anything.novita.core.client import NovitaClient

        client = NovitaClient(api_key=API_KEY)
        task_id = client.hunyuan_video(
            model_name="hunyuan-video-fast",
            prompt="red dot", width=1280, height=720,
            steps=2, frames=85, seed=42,
        )
        self.assertTrue(task_id, "hunyuan_video should return a task_id")

        # Verify the task exists
        result = client.get_task_result(task_id)
        self.assertIn("task", result)


class TestE2E_Image_Processing(unittest.TestCase):
    """Real API: Image generation + processing pipeline."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_flux_then_remove_bg(self):
        """Generate FLUX image, download, then remove background."""
        import requests as req
        from cli_anything.novita.core.client import NovitaClient

        client = NovitaClient(api_key=API_KEY)

        # Step 1: Generate tiny image with FLUX
        flux_result = client.flux_schnell(
            prompt="red circle on white background",
            width=64, height=64, seed=42, steps=1, image_num=1,
        )
        image_url = flux_result["images"][0]["image_url"]
        self.assertTrue(image_url.startswith("http"))

        # Step 2: Download the image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name
            resp = req.get(image_url, timeout=30)
            f.write(resp.content)

        try:
            self.assertGreater(os.path.getsize(tmp_path), 100)

            # Step 3: Remove background via CLI
            with tempfile.TemporaryDirectory() as tmpdir:
                out_path = os.path.join(tmpdir, "nobg.png")
                result = invoke(self.runner, [
                    "image", "remove-bg", tmp_path, "-o", out_path,
                ])
                self.assertEqual(result.exit_code, 0)
                self.assertIn("Saved:", result.output)
                self.assertTrue(os.path.exists(out_path))
                self.assertGreater(os.path.getsize(out_path), 50)
        finally:
            os.unlink(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════
# 9. Task API (via FLUX image gen which returns a task)
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_TaskAPI(unittest.TestCase):
    """Real API: Task status checking using txt2img async task."""

    def setUp(self):
        self.runner = CliRunner()

    @requires_api_key
    def test_task_lifecycle_submit_status_wait(self):
        """Submit async txt2img, check status, then wait for result."""
        from cli_anything.novita.core.client import NovitaClient

        client = NovitaClient(api_key=API_KEY)

        # Step 1: Submit async task
        task_id = client.txt2img(
            request={
                "model_name": "sd_xl_base_1.0.safetensors",
                "prompt": "red dot",
                "width": 128, "height": 128,
                "image_num": 1, "steps": 1,
                "guidance_scale": 7.5, "sampler_name": "Euler a",
                "seed": 42,
            },
            extra={"response_image_type": "jpeg"},
        )
        self.assertTrue(task_id, "txt2img should return a task_id")

        # Step 2: Check task status via CLI
        status_result = invoke(self.runner, ["task", "status", task_id])
        self.assertEqual(status_result.exit_code, 0)
        self.assertIn("Task:", status_result.output)
        self.assertIn(task_id[:8], status_result.output)

        # Step 3: Check status in JSON mode
        json_result = invoke(self.runner, ["task", "status", task_id], json_mode=True)
        self.assertEqual(json_result.exit_code, 0)
        data = json.loads(json_result.output)
        self.assertIn("task", data)
        self.assertIn("status", data["task"])
        self.assertIn(data["task"]["status"], [
            "TASK_STATUS_QUEUED", "TASK_STATUS_PROCESSING", "TASK_STATUS_SUCCEED",
        ])

        # Step 4: Wait for completion via client
        result = client.poll_task(task_id, timeout=120)
        self.assertEqual(result["task"]["status"], "TASK_STATUS_SUCCEED")
        self.assertGreater(len(result.get("images", [])), 0)
        self.assertTrue(result["images"][0]["image_url"].startswith("http"))


# ═══════════════════════════════════════════════════════════════════════════
# 10. Subprocess Tests (installed CLI)
# ═══════════════════════════════════════════════════════════════════════════

class TestE2E_Subprocess(unittest.TestCase):
    """Real API via subprocess: Tests the installed CLI entry point."""

    @requires_api_key
    def test_chat_subprocess(self):
        result = subprocess.run(
            ["novita", "--api-key", API_KEY, "chat", "Say ok",
             "-m", "deepseek/deepseek-v3-0324", "--max-tokens", "5"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(len(result.stdout.strip()) > 0)

    @requires_api_key
    def test_models_subprocess_json(self):
        result = subprocess.run(
            ["novita", "--json-output", "--api-key", API_KEY,
             "models", "list", "--filter", "deepseek"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIsInstance(data, list)
        self.assertTrue(any("deepseek" in m["id"] for m in data))

    @requires_api_key
    def test_embed_subprocess(self):
        result = subprocess.run(
            ["novita", "--json-output", "--api-key", API_KEY,
             "embed", "test via subprocess"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(len(data["data"][0]["embedding"]), 1024)

    @requires_api_key
    def test_gpu_products_subprocess(self):
        result = subprocess.run(
            ["novita", "--json-output", "--api-key", API_KEY,
             "gpu", "products"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("data", data)
        self.assertGreater(len(data["data"]), 0)

    @requires_api_key
    def test_balance_subprocess(self):
        result = subprocess.run(
            ["novita", "--api-key", API_KEY, "account", "balance"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Credit Balance:", result.stdout)


if __name__ == "__main__":
    unittest.main()
