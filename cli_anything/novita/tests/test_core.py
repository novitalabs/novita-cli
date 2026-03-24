"""Unit tests for Novita AI CLI core modules."""

import json
import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from cli_anything.novita.core.client import NovitaClient, NovitaError, BASE_URL
from cli_anything.novita.utils.output import format_balance, format_table
from cli_anything.novita.novita_cli import cli


class TestNovitaClient(unittest.TestCase):
    """Test NovitaClient initialization and error handling."""

    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("NOVITA_API_KEY", None)
            with self.assertRaises(NovitaError):
                NovitaClient(api_key="")

    def test_client_init_with_key(self):
        client = NovitaClient(api_key="test-key")
        self.assertEqual(client.api_key, "test-key")
        self.assertIn("Bearer test-key", client.session.headers["Authorization"])

    def test_client_init_from_env(self):
        with patch.dict(os.environ, {"NOVITA_API_KEY": "env-key"}):
            client = NovitaClient()
            self.assertEqual(client.api_key, "env-key")


class TestNovitaError(unittest.TestCase):
    """Test error class."""

    def test_error_attributes(self):
        err = NovitaError("bad request", status_code=400, error_code="INVALID")
        self.assertEqual(str(err), "bad request")
        self.assertEqual(err.status_code, 400)
        self.assertEqual(err.error_code, "INVALID")


class TestOutputUtils(unittest.TestCase):
    """Test output formatting."""

    def test_format_balance(self):
        self.assertEqual(format_balance("10000"), "$1.0000")
        self.assertEqual(format_balance("497975"), "$49.7975")
        self.assertEqual(format_balance("0"), "$0.0000")

    def test_format_balance_invalid(self):
        self.assertEqual(format_balance("abc"), "abc")
        self.assertEqual(format_balance(None), None)

    def test_format_table_empty(self):
        self.assertEqual(format_table([], ["A", "B"]), "(no data)")

    def test_format_table_data(self):
        rows = [["hello", "world"], ["foo", "bar"]]
        result = format_table(rows, ["Col1", "Col2"])
        self.assertIn("hello", result)
        self.assertIn("Col1", result)


class TestCLIHelp(unittest.TestCase):
    """Test CLI commands emit help text."""

    def setUp(self):
        self.runner = CliRunner()

    def test_root_help(self):
        result = self.runner.invoke(cli, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Novita AI CLI", result.output)

    def test_chat_help(self):
        result = self.runner.invoke(cli, ["chat", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--model", result.output)

    def test_models_help(self):
        result = self.runner.invoke(cli, ["models", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("list", result.output)

    def test_image_help(self):
        result = self.runner.invoke(cli, ["image", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("generate", result.output)
        self.assertIn("flux", result.output)
        self.assertIn("upscale", result.output)
        self.assertIn("remove-bg", result.output)

    def test_video_help(self):
        result = self.runner.invoke(cli, ["video", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("generate", result.output)
        self.assertIn("from-image", result.output)
        self.assertIn("hunyuan", result.output)

    def test_audio_help(self):
        result = self.runner.invoke(cli, ["audio", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("tts", result.output)
        self.assertIn("asr", result.output)

    def test_account_help(self):
        result = self.runner.invoke(cli, ["account", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("balance", result.output)
        self.assertIn("billing", result.output)

    def test_task_help(self):
        result = self.runner.invoke(cli, ["task", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("status", result.output)
        self.assertIn("wait", result.output)

    def test_batch_help(self):
        result = self.runner.invoke(cli, ["batch", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("create", result.output)
        self.assertIn("list", result.output)

    def test_embed_help(self):
        result = self.runner.invoke(cli, ["embed", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--model", result.output)

    def test_rerank_help(self):
        result = self.runner.invoke(cli, ["rerank", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--document", result.output)

    def test_complete_help(self):
        result = self.runner.invoke(cli, ["complete", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--model", result.output)

    def test_gpu_help(self):
        result = self.runner.invoke(cli, ["gpu", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("list", result.output)
        self.assertIn("create", result.output)
        self.assertIn("start", result.output)
        self.assertIn("stop", result.output)
        self.assertIn("delete", result.output)
        self.assertIn("products", result.output)
        self.assertIn("metrics", result.output)
        self.assertIn("edit", result.output)

    def test_template_help(self):
        result = self.runner.invoke(cli, ["template", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("list", result.output)
        self.assertIn("create", result.output)
        self.assertIn("delete", result.output)
        self.assertIn("get", result.output)

    def test_serverless_help(self):
        result = self.runner.invoke(cli, ["serverless", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("list", result.output)
        self.assertIn("create", result.output)
        self.assertIn("get", result.output)
        self.assertIn("update", result.output)
        self.assertIn("delete", result.output)


class TestCLIMocked(unittest.TestCase):
    """Test CLI commands with mocked API calls."""

    def setUp(self):
        self.runner = CliRunner()

    @patch("cli_anything.novita.novita_cli.NovitaClient")
    def test_models_list_json(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.list_models.return_value = {
            "data": [
                {"id": "test-model", "context_size": 4096,
                 "input_token_price_per_m": 100, "output_token_price_per_m": 200}
            ]
        }
        result = self.runner.invoke(cli, ["--json-output", "--api-key", "fake", "models", "list"], obj={})
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertEqual(data[0]["id"], "test-model")

    @patch("cli_anything.novita.novita_cli.NovitaClient")
    def test_account_balance_json(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.get_balance.return_value = {"credit_balance": 50000, "allow_features": ["upload_model"]}
        result = self.runner.invoke(cli, ["--json-output", "--api-key", "fake", "account", "balance"], obj={})
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertEqual(data["credit_balance"], 50000)

    @patch("cli_anything.novita.novita_cli.NovitaClient")
    def test_embed_json(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.embeddings.return_value = {
            "data": [{"index": 0, "embedding": [0.1, 0.2], "object": "embedding"}],
            "usage": {"prompt_tokens": 2, "total_tokens": 2},
        }
        result = self.runner.invoke(cli, ["--json-output", "--api-key", "fake", "embed", "test"], obj={})
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertEqual(len(data["data"][0]["embedding"]), 2)

    @patch("cli_anything.novita.novita_cli.NovitaClient")
    def test_gpu_list_json(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.gpu_list_instances.return_value = {
            "instances": [
                {"id": "inst-123", "name": "test-gpu", "status": "running",
                 "productName": "A100", "gpuNum": 1, "billingMode": "onDemand"}
            ],
            "total": 1,
        }
        result = self.runner.invoke(cli, ["--json-output", "--api-key", "fake", "gpu", "list"], obj={})
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertEqual(data["instances"][0]["name"], "test-gpu")

    @patch("cli_anything.novita.novita_cli.NovitaClient")
    def test_gpu_products_json(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.gpu_list_products.return_value = {
            "data": [{"id": "prod-1", "name": "A100-80G", "cpuPerGpu": 8,
                       "memoryPerGpu": 64, "price": 100, "availableDeploy": True}]
        }
        result = self.runner.invoke(cli, ["--json-output", "--api-key", "fake", "gpu", "products"], obj={})
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertEqual(data["data"][0]["name"], "A100-80G")

    @patch("cli_anything.novita.novita_cli.NovitaClient")
    def test_serverless_list_json(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.serverless_list_endpoints.return_value = {
            "endpoints": [
                {"id": "ep-123", "name": "my-endpoint", "state": {"state": "running"}, "url": "https://example.com"}
            ],
            "total": 1,
        }
        result = self.runner.invoke(cli, ["--json-output", "--api-key", "fake", "serverless", "list"], obj={})
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertEqual(data["endpoints"][0]["name"], "my-endpoint")

    @patch("cli_anything.novita.novita_cli.NovitaClient")
    def test_template_list_json(self, MockClient):
        mock_instance = MockClient.return_value
        mock_instance.gpu_list_templates.return_value = {
            "template": [{"Id": "tmpl-1", "name": "pytorch", "image": "pytorch:latest", "rootfsSize": 40}],
            "total": 1,
        }
        result = self.runner.invoke(cli, ["--json-output", "--api-key", "fake", "template", "list"], obj={})
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        self.assertEqual(data["template"][0]["name"], "pytorch")


class TestCLISubprocess(unittest.TestCase):
    """Test CLI via subprocess to verify installed entry point works."""

    @staticmethod
    def _resolve_cli(name="cli-anything-novita"):
        import shutil
        path = shutil.which(name)
        if path or os.environ.get("CLI_ANYTHING_FORCE_INSTALLED"):
            return name
        return [sys.executable, "-m", "cli_anything.novita.novita_cli"]

    def test_help_subprocess(self):
        cmd = self._resolve_cli()
        if isinstance(cmd, list):
            result = subprocess.run(cmd + ["--help"], capture_output=True, text=True)
        else:
            result = subprocess.run([cmd, "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Novita AI CLI", result.stdout)

    def test_version_in_output(self):
        cmd = self._resolve_cli("novita")
        if isinstance(cmd, list):
            result = subprocess.run(cmd + ["--help"], capture_output=True, text=True)
        else:
            result = subprocess.run([cmd, "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Commands:", result.stdout)


if __name__ == "__main__":
    unittest.main()
