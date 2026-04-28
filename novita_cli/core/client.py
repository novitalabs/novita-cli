"""Core HTTP client for Novita AI API."""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

import requests


BASE_URL = "https://api.novita.ai"
OPENAI_BASE = f"{BASE_URL}/v3/openai"
OPENAI_V1_BASE = f"{BASE_URL}/openai/v1"

DEFAULT_POLL_INTERVAL = 3
DEFAULT_POLL_TIMEOUT = 600


class NovitaError(Exception):
    """Novita API error."""

    def __init__(self, message: str, status_code: int = 0, error_code: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class NovitaClient:
    """HTTP client for Novita AI APIs."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("NOVITA_API_KEY", "")
        if not self.api_key:
            raise NovitaError(
                "API key required. Set NOVITA_API_KEY env var or pass --api-key."
            )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def _request(
        self, method: str, url: str, json_data: Optional[Dict] = None,
        params: Optional[Dict] = None, stream: bool = False,
    ) -> requests.Response:
        resp = self.session.request(
            method, url, json=json_data, params=params, stream=stream, timeout=120,
        )
        if not stream and resp.status_code >= 400:
            try:
                err = resp.json()
                msg = err.get("error", {}).get("message", resp.text)
                code = err.get("error", {}).get("code", "")
            except (json.JSONDecodeError, AttributeError):
                msg = resp.text
                code = ""
            raise NovitaError(msg, resp.status_code, code)
        return resp

    def get(self, path: str, params: Optional[Dict] = None) -> Dict:
        url = f"{BASE_URL}{path}"
        return self._request("GET", url, params=params).json()

    def post(self, path: str, data: Dict, stream: bool = False) -> Any:
        url = f"{BASE_URL}{path}"
        resp = self._request("POST", url, json_data=data, stream=stream)
        if stream:
            return resp
        return resp.json()

    def post_openai(self, path: str, data: Dict, stream: bool = False) -> Any:
        url = f"{OPENAI_BASE}{path}"
        resp = self._request("POST", url, json_data=data, stream=stream)
        if stream:
            return resp
        return resp.json()

    def get_openai(self, path: str, params: Optional[Dict] = None) -> Dict:
        url = f"{OPENAI_BASE}{path}"
        return self._request("GET", url, params=params).json()

    def stream_sse(self, resp: requests.Response) -> Iterator[Dict]:
        """Iterate SSE events from a streaming response."""
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data = line[6:]
            if data.strip() == "[DONE]":
                return
            try:
                yield json.loads(data)
            except json.JSONDecodeError:
                continue

    def poll_task(
        self,
        task_id: str,
        interval: int = DEFAULT_POLL_INTERVAL,
        timeout: int = DEFAULT_POLL_TIMEOUT,
        progress_callback=None,
    ) -> Dict:
        """Poll an async task until completion."""
        start = time.time()
        while True:
            result = self.get("/v3/async/task-result", params={"task_id": task_id})
            status = result.get("task", {}).get("status", "")
            progress = result.get("task", {}).get("progress_percent", 0)

            if progress_callback:
                progress_callback(status, progress)

            if status == "TASK_STATUS_SUCCEED":
                return result
            if status == "TASK_STATUS_FAILED":
                reason = result.get("task", {}).get("reason", "Unknown error")
                raise NovitaError(f"Task failed: {reason}")

            if time.time() - start > timeout:
                raise NovitaError(f"Task timed out after {timeout}s")

            time.sleep(interval)

    # --- LLM APIs ---

    def chat_completion(self, **kwargs) -> Dict:
        stream = kwargs.get("stream", False)
        return self.post_openai("/chat/completions", kwargs, stream=stream)

    def completion(self, **kwargs) -> Dict:
        stream = kwargs.get("stream", False)
        return self.post_openai("/completions", kwargs, stream=stream)

    def embeddings(self, **kwargs) -> Dict:
        return self.post_openai("/embeddings", kwargs)

    def rerank(self, **kwargs) -> Dict:
        return self.post_openai("/rerank", kwargs)

    def list_models(self) -> Dict:
        return self.get_openai("/models")

    def retrieve_model(self, model_id: str) -> Dict:
        return self.get_openai(f"/models/{model_id}")

    # --- Image APIs ---

    def txt2img(self, request: Dict, extra: Optional[Dict] = None) -> str:
        data = {"request": request}
        if extra:
            data["extra"] = extra
        result = self.post("/v3/async/txt2img", data)
        return result.get("task_id", "")

    def img2img(self, request: Dict, extra: Optional[Dict] = None) -> str:
        data = {"request": request}
        if extra:
            data["extra"] = extra
        result = self.post("/v3/async/img2img", data)
        return result.get("task_id", "")

    def flux_schnell(self, **kwargs) -> Dict:
        return self.post("/v3beta/flux-1-schnell", kwargs)

    def upscale(self, request: Dict, extra: Optional[Dict] = None) -> str:
        data = {"request": request}
        if extra:
            data["extra"] = extra
        result = self.post("/v3/async/upscale", data)
        return result.get("task_id", "")

    def remove_background(self, image_file: str, extra: Optional[Dict] = None) -> Dict:
        data = {"image_file": image_file}
        if extra:
            data["extra"] = extra
        return self.post("/v3/remove-background", data)

    def replace_background(self, image_file: str, prompt: str, extra: Optional[Dict] = None) -> str:
        data = {"image_file": image_file, "prompt": prompt}
        if extra:
            data["extra"] = extra
        result = self.post("/v3/async/replace-background", data)
        return result.get("task_id", "")

    def inpainting(self, request: Dict, extra: Optional[Dict] = None) -> str:
        data = {"request": request}
        if extra:
            data["extra"] = extra
        result = self.post("/v3/async/inpainting", data)
        return result.get("task_id", "")

    def reimagine(self, image_file: str, extra: Optional[Dict] = None) -> Dict:
        data = {"image_file": image_file}
        if extra:
            data["extra"] = extra
        return self.post("/v3/reimagine", data)

    def img2prompt(self, image_file: str) -> Dict:
        return self.post("/v3/img2prompt", {"image_file": image_file})

    def merge_face(self, face_image_file: str, image_file: str, extra: Optional[Dict] = None) -> Dict:
        data = {"face_image_file": face_image_file, "image_file": image_file}
        if extra:
            data["extra"] = extra
        return self.post("/v3/merge-face", data)

    def cleanup(self, image_file: str, mask_file: str, extra: Optional[Dict] = None) -> Dict:
        data = {"image_file": image_file, "mask_file": mask_file}
        if extra:
            data["extra"] = extra
        return self.post("/v3/cleanup", data)

    def outpainting(self, image_file: str, prompt: str, width: int, height: int,
                    center_x: int, center_y: int, extra: Optional[Dict] = None) -> Dict:
        data = {
            "image_file": image_file, "prompt": prompt,
            "width": width, "height": height,
            "center_x": center_x, "center_y": center_y,
        }
        if extra:
            data["extra"] = extra
        return self.post("/v3/outpainting", data)

    def remove_text(self, image_file: str, extra: Optional[Dict] = None) -> Dict:
        data = {"image_file": image_file}
        if extra:
            data["extra"] = extra
        return self.post("/v3/remove-text", data)

    # --- Video APIs ---

    def txt2video(self, request: Dict, extra: Optional[Dict] = None) -> str:
        data = {**request}
        if extra:
            data["extra"] = extra
        result = self.post("/v3/async/txt2video", data)
        return result.get("task_id", "")

    def img2video(self, **kwargs) -> str:
        result = self.post("/v3/async/img2video", kwargs)
        return result.get("task_id", "")

    def hunyuan_video(self, **kwargs) -> str:
        result = self.post("/v3/async/hunyuan-video-fast", kwargs)
        return result.get("task_id", "")

    # --- Audio APIs ---

    def minimax_tts(self, **kwargs) -> Any:
        stream = kwargs.get("stream", False)
        return self.post("/v3/minimax-speech-02-hd", kwargs, stream=stream)

    def glm_tts(self, **kwargs) -> Any:
        """GLM TTS returns binary audio data, not JSON."""
        url = f"{BASE_URL}/v3/glm-tts"
        resp = self._request("POST", url, json_data=kwargs)
        content_type = resp.headers.get("Content-Type", "")
        if "audio" in content_type:
            return {"audio_data": resp.content, "content_type": content_type}
        return resp.json()

    def glm_asr(self, **kwargs) -> Dict:
        return self.post("/v3/glm-asr", kwargs)

    def voice_clone(self, audio_url: str, **kwargs) -> Dict:
        data = {"audio_url": audio_url, **kwargs}
        return self.post("/v3/minimax-voice-cloning", data)

    # --- Account APIs ---

    def get_balance(self) -> Dict:
        return self.get("/v3/user")

    def get_monthly_bill(self) -> Dict:
        return self.get("/v3/user/monthly-bill")

    def get_usage_billing(self) -> Dict:
        return self.get("/v3/user/usage-based-billing")

    def get_fixed_billing(self) -> Dict:
        return self.get("/v3/user/fixed-term-billing")

    # --- Task API ---

    def get_task_result(self, task_id: str) -> Dict:
        return self.get("/v3/async/task-result", params={"task_id": task_id})

    # --- Batch APIs (use /openai/v1 base) ---

    def _get_v1(self, path: str, params: Optional[Dict] = None) -> Dict:
        url = f"{OPENAI_V1_BASE}{path}"
        return self._request("GET", url, params=params).json()

    def _post_v1(self, path: str, data: Dict) -> Dict:
        url = f"{OPENAI_V1_BASE}{path}"
        return self._request("POST", url, json_data=data).json()

    def list_files(self) -> Dict:
        return self._get_v1("/files")

    def retrieve_file(self, file_id: str) -> Dict:
        return self._get_v1(f"/files/{file_id}")

    def delete_file(self, file_id: str) -> Dict:
        url = f"{OPENAI_V1_BASE}/files/{file_id}"
        return self._request("DELETE", url).json()

    def retrieve_file_content(self, file_id: str) -> str:
        url = f"{OPENAI_V1_BASE}/files/{file_id}/content"
        resp = self._request("GET", url)
        return resp.text

    def create_batch(self, **kwargs) -> Dict:
        return self._post_v1("/batches", kwargs)

    def list_batches(self) -> Dict:
        return self._get_v1("/batches")

    def retrieve_batch(self, batch_id: str) -> Dict:
        return self._get_v1(f"/batches/{batch_id}")

    def cancel_batch(self, batch_id: str) -> Dict:
        return self._post_v1(f"/batches/{batch_id}/cancel", {})

    def upload_batch_file(self, file_path: str) -> Dict:
        """Upload a JSONL file for batch processing."""
        url = f"{OPENAI_V1_BASE}/files"
        # Must remove Content-Type header so requests sets multipart boundary
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with open(file_path, "rb") as f:
            resp = requests.post(
                url, files={"file": f}, data={"purpose": "batch"},
                headers=headers, timeout=120,
            )
        if resp.status_code >= 400:
            raise NovitaError(resp.text, resp.status_code)
        return resp.json()

    # --- GPU Instance APIs ---

    GPU_BASE = "/gpu-instance/openapi/v1"

    def gpu_create_instance(self, **kwargs) -> Dict:
        return self.post(f"{self.GPU_BASE}/gpu/instance/create", kwargs)

    def gpu_list_instances(self, page_size: int = 20, page_num: int = 0, **kwargs) -> Dict:
        params = {"pageSize": page_size, "pageNum": page_num, **kwargs}
        return self.get(f"{self.GPU_BASE}/gpu/instances", params=params)

    def gpu_get_instance(self, instance_id: str) -> Dict:
        return self.get(f"{self.GPU_BASE}/gpu/instance", params={"instanceId": instance_id})

    def gpu_start_instance(self, instance_id: str) -> Dict:
        return self.post(f"{self.GPU_BASE}/gpu/instance/start", {"instanceId": instance_id})

    def gpu_stop_instance(self, instance_id: str) -> Dict:
        return self.post(f"{self.GPU_BASE}/gpu/instance/stop", {"instanceId": instance_id})

    def gpu_delete_instance(self, instance_id: str) -> Dict:
        return self.post(f"{self.GPU_BASE}/gpu/instance/delete", {"instanceId": instance_id})

    def gpu_restart_instance(self, instance_id: str) -> Dict:
        return self.post(f"{self.GPU_BASE}/gpu/instance/restart", {"instanceId": instance_id})

    def gpu_list_clusters(self) -> Dict:
        return self.get(f"{self.GPU_BASE}/clusters")

    def gpu_edit_instance(self, instance_id: str, **kwargs) -> Dict:
        return self.post(f"{self.GPU_BASE}/gpu/instance/edit", {"instanceId": instance_id, **kwargs})

    def gpu_list_products(self, **kwargs) -> Dict:
        return self.get(f"{self.GPU_BASE}/products", params=kwargs)

    def gpu_list_cpu_products(self, **kwargs) -> Dict:
        return self.get(f"{self.GPU_BASE}/cpu/products", params=kwargs)

    def gpu_get_metrics(self, instance_id: str, **kwargs) -> Dict:
        params = {"instanceId": instance_id, **kwargs}
        return self.get("/openapi/v1/metrics/gpu/instance", params=params)

    # --- GPU Template APIs ---

    def gpu_create_template(self, template: Dict) -> Dict:
        return self.post(f"{self.GPU_BASE}/template/create", {"template": template})

    def gpu_list_templates(self, channel: str = "private", is_my_community: bool = True,
                           page_size: int = 20, page_num: int = 0, **kwargs) -> Dict:
        params = {"channel": channel, "isMyCommunity": is_my_community,
                  "pageSize": page_size, "pageNum": page_num, **kwargs}
        return self.get(f"{self.GPU_BASE}/templates", params=params)

    def gpu_get_template(self, template_id: str) -> Dict:
        result = self.get(f"{self.GPU_BASE}/template", params={"templateId": template_id})
        return result.get("template", result)

    def gpu_edit_template(self, template: Dict) -> Dict:
        return self.post(f"{self.GPU_BASE}/template/update", {"template": template})

    def gpu_delete_template(self, template_id: str) -> Dict:
        return self.post(f"{self.GPU_BASE}/template/delete", {"templateId": template_id})

    # --- Network Storage ---

    def gpu_create_storage(self, cluster_id: str, name: str, size: int) -> Dict:
        return self.post(f"{self.GPU_BASE}/networkstorage/create",
                         {"clusterId": cluster_id, "storageName": name, "storageSize": size})

    def gpu_list_storage(self, **kwargs) -> Dict:
        return self.get(f"{self.GPU_BASE}/networkstorages", params=kwargs)

    def gpu_delete_storage(self, storage_id: str) -> Dict:
        return self.post(f"{self.GPU_BASE}/networkstorage/delete", {"id": storage_id})

    # --- Serverless APIs ---

    SL_BASE = "/gpu-instance/openapi/v1"

    def serverless_create_endpoint(self, endpoint: Dict) -> Dict:
        return self.post(f"{self.SL_BASE}/endpoint/create", {"endpoint": endpoint})

    def serverless_list_endpoints(self, page_size: int = 20, page_num: int = 0) -> Dict:
        return self.get(f"{self.SL_BASE}/endpoints", params={"pageSize": page_size, "pageNum": page_num})

    def serverless_get_endpoint(self, endpoint_id: str) -> Dict:
        return self.get(f"{self.SL_BASE}/endpoint", params={"id": endpoint_id})

    def serverless_update_endpoint(self, **kwargs) -> Dict:
        return self.post(f"{self.SL_BASE}/endpoint/update", kwargs)

    def serverless_delete_endpoint(self, endpoint_id: str) -> Dict:
        return self.post(f"{self.SL_BASE}/endpoint/delete", {"name": endpoint_id})
