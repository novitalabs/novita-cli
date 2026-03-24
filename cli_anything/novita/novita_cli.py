"""Novita AI CLI - Main entry point."""

import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional

import click

from cli_anything.novita.core.client import NovitaClient, NovitaError
from cli_anything.novita.utils.output import (
    format_balance,
    format_table,
    output_error,
    output_json,
    output_progress,
    output_stream_chunk,
    output_text,
)


def get_client(ctx) -> NovitaClient:
    """Get or create the API client from Click context."""
    if "client" not in ctx.obj:
        ctx.obj["client"] = NovitaClient(api_key=ctx.obj.get("api_key"))
    return ctx.obj["client"]


def read_image_file(path: str) -> str:
    """Read an image file and return base64-encoded string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def download_url(url: str, output_path: str):
    """Download a URL to a local file."""
    import requests
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)


# ── Root Group ──────────────────────────────────────────────────────────────

@click.group()
@click.option("--api-key", envvar="NOVITA_API_KEY", help="Novita AI API key")
@click.option("--json-output", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(ctx, api_key, json_mode):
    """Novita AI CLI - Access all Novita AI APIs from the command line."""
    ctx.ensure_object(dict)
    ctx.obj["api_key"] = api_key
    ctx.obj["json"] = json_mode


# ── Chat ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("message")
@click.option("-m", "--model", default="deepseek/deepseek-v3-0324", help="Model name")
@click.option("--system", "system_prompt", default=None, help="System prompt")
@click.option("--max-tokens", default=1024, type=int, help="Max tokens")
@click.option("--temperature", default=1.0, type=float, help="Temperature (0-2)")
@click.option("--top-p", default=None, type=float, help="Top-p sampling")
@click.option("--stream/--no-stream", default=True, help="Stream output")
@click.option("--json-schema", default=None, help="JSON schema for structured output")
@click.pass_context
def chat(ctx, message, model, system_prompt, max_tokens, temperature, top_p, stream, json_schema):
    """Send a chat completion request.

    Example: novita chat "What is Python?" -m deepseek/deepseek-r1
    """
    client = get_client(ctx)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})

    kwargs = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }
    if top_p is not None:
        kwargs["top_p"] = top_p
    if json_schema:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "response", "schema": json.loads(json_schema)},
        }

    try:
        if stream and not ctx.obj.get("json"):
            resp = client.chat_completion(**kwargs)
            full_content = ""
            for chunk in client.stream_sse(resp):
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    output_stream_chunk(content)
                    full_content += content
            output_stream_chunk("", end="\n")
        else:
            kwargs["stream"] = False
            result = client.chat_completion(**kwargs)
            if ctx.obj.get("json"):
                output_json(result)
            else:
                content = result["choices"][0]["message"]["content"]
                output_text(content)
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Complete ────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("prompt")
@click.option("-m", "--model", default="deepseek/deepseek-v3-0324", help="Model name")
@click.option("--max-tokens", default=512, type=int, help="Max tokens")
@click.option("--temperature", default=1.0, type=float, help="Temperature")
@click.option("--stream/--no-stream", default=False, help="Stream output")
@click.pass_context
def complete(ctx, prompt, model, max_tokens, temperature, stream):
    """Text completion (legacy).

    Example: novita complete "Once upon a time"
    """
    client = get_client(ctx)
    kwargs = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }
    try:
        if stream and not ctx.obj.get("json"):
            resp = client.completion(**kwargs)
            for chunk in client.stream_sse(resp):
                text = chunk.get("choices", [{}])[0].get("text", "")
                if text:
                    output_stream_chunk(text)
            output_stream_chunk("", end="\n")
        else:
            kwargs["stream"] = False
            result = client.completion(**kwargs)
            if ctx.obj.get("json"):
                output_json(result)
            else:
                output_text(result["choices"][0]["text"])
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Embeddings ──────────────────────────────────────────────────────────────

@cli.command()
@click.argument("text")
@click.option("-m", "--model", default="baai/bge-m3", help="Embedding model")
@click.pass_context
def embed(ctx, text, model):
    """Generate text embeddings.

    Example: novita embed "Hello world"
    """
    client = get_client(ctx)
    try:
        result = client.embeddings(input=text, model=model)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            vec = result["data"][0]["embedding"]
            output_text(f"Dimensions: {len(vec)}")
            output_text(f"First 5: {vec[:5]}")
            output_text(f"Usage: {result.get('usage', {})}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Rerank ──────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("query")
@click.option("-d", "--document", "documents", multiple=True, required=True, help="Documents to rank")
@click.option("-m", "--model", default="baai/bge-reranker-v2-m3", help="Rerank model")
@click.option("--top-n", default=None, type=int, help="Return top N results")
@click.pass_context
def rerank(ctx, query, documents, model, top_n):
    """Rerank documents by relevance to a query.

    Example: novita rerank "best pet" -d "cats are cute" -d "dogs are loyal" -d "fish swim"
    """
    client = get_client(ctx)
    kwargs = {"model": model, "query": query, "documents": list(documents)}
    if top_n:
        kwargs["top_n"] = top_n
    try:
        result = client.rerank(**kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            for r in result.get("results", []):
                score = r.get("relevance_score", 0)
                idx = r.get("index", 0)
                doc = r.get("document", {}).get("text", documents[idx] if idx < len(documents) else "")
                output_text(f"  [{score:.4f}] {doc}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Models ──────────────────────────────────────────────────────────────────

@cli.group()
def models():
    """List and inspect available models."""
    pass


@models.command("list")
@click.option("--filter", "name_filter", default=None, help="Filter by name substring")
@click.pass_context
def models_list(ctx, name_filter):
    """List all available LLM models.

    Example: novita models list --filter deepseek
    """
    client = get_client(ctx)
    try:
        result = client.list_models()
        data = result.get("data", [])
        if name_filter:
            data = [m for m in data if name_filter.lower() in m.get("id", "").lower()]
        if ctx.obj.get("json"):
            output_json(data)
        else:
            rows = []
            for m in data:
                rows.append([
                    m.get("id", ""),
                    str(m.get("context_size", "")),
                    str(m.get("input_token_price_per_m", "")),
                    str(m.get("output_token_price_per_m", "")),
                ])
            output_text(format_table(rows, ["Model ID", "Context", "In $/M", "Out $/M"]))
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@models.command("get")
@click.argument("model_id")
@click.pass_context
def models_get(ctx, model_id):
    """Get details for a specific model.

    Example: novita models get deepseek/deepseek-r1
    """
    client = get_client(ctx)
    try:
        result = client.retrieve_model(model_id)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            for k, v in result.items():
                output_text(f"  {k}: {v}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Image Generation ────────────────────────────────────────────────────────

@cli.group()
def image():
    """Image generation and editing commands."""
    pass


@image.command("generate")
@click.argument("prompt")
@click.option("-m", "--model", default="sd_xl_base_1.0.safetensors", help="Model name")
@click.option("-W", "--width", default=1024, type=int, help="Width (128-2048)")
@click.option("-H", "--height", default=1024, type=int, help="Height (128-2048)")
@click.option("-n", "--num", default=1, type=int, help="Number of images (1-8)")
@click.option("--steps", default=20, type=int, help="Inference steps (1-100)")
@click.option("--cfg", "guidance_scale", default=7.5, type=float, help="Guidance scale (1-30)")
@click.option("--sampler", default="Euler a", help="Sampler name")
@click.option("--negative", default="", help="Negative prompt")
@click.option("--seed", default=-1, type=int, help="Random seed")
@click.option("-o", "--output", "output_dir", default=".", help="Output directory")
@click.option("--format", "img_format", default="png", type=click.Choice(["png", "webp", "jpeg"]))
@click.option("--no-wait", is_flag=True, help="Return task_id without waiting")
@click.pass_context
def image_generate(ctx, prompt, model, width, height, num, steps, guidance_scale,
                   sampler, negative, seed, output_dir, img_format, no_wait):
    """Generate images from text (Stable Diffusion).

    Example: novita image generate "a cute cat" -W 512 -H 512
    """
    client = get_client(ctx)
    request = {
        "model_name": model,
        "prompt": prompt,
        "width": width,
        "height": height,
        "image_num": num,
        "steps": steps,
        "guidance_scale": guidance_scale,
        "sampler_name": sampler,
        "seed": seed,
    }
    if negative:
        request["negative_prompt"] = negative
    extra = {"response_image_type": img_format}

    try:
        task_id = client.txt2img(request, extra)
        if no_wait or ctx.obj.get("json") and no_wait:
            output_json({"task_id": task_id}) if ctx.obj.get("json") else output_text(f"Task ID: {task_id}")
            return

        output_text(f"Task submitted: {task_id}")
        result = client.poll_task(task_id, progress_callback=output_progress if not ctx.obj.get("json") else None)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            images = result.get("images", [])
            os.makedirs(output_dir, exist_ok=True)
            for i, img in enumerate(images):
                url = img.get("image_url", "")
                ext = img.get("image_type", img_format)
                out_path = os.path.join(output_dir, f"novita_img_{task_id[:8]}_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("flux")
@click.argument("prompt")
@click.option("-W", "--width", default=512, type=int, help="Width")
@click.option("-H", "--height", default=512, type=int, help="Height")
@click.option("-n", "--num", default=1, type=int, help="Number of images")
@click.option("--steps", default=4, type=int, help="Steps")
@click.option("--seed", default=2024, type=int, help="Seed")
@click.option("-o", "--output", "output_dir", default=".", help="Output directory")
@click.pass_context
def image_flux(ctx, prompt, width, height, num, steps, seed, output_dir):
    """Generate images with FLUX.1 Schnell (fast, sync).

    Example: novita image flux "a sunset over mountains"
    """
    client = get_client(ctx)
    try:
        result = client.flux_schnell(
            prompt=prompt, width=width, height=height,
            image_num=num, steps=steps, seed=seed,
        )
        if ctx.obj.get("json"):
            output_json(result)
        else:
            images = result.get("images", [])
            os.makedirs(output_dir, exist_ok=True)
            for i, img in enumerate(images):
                url = img.get("image_url", "")
                ext = img.get("image_type", "png")
                out_path = os.path.join(output_dir, f"novita_flux_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("upscale")
@click.argument("image_path")
@click.option("-m", "--model", default="RealESRGAN_x4plus_anime_6B", help="Upscale model")
@click.option("--scale", default=2.0, type=float, help="Scale factor (1-4)")
@click.option("-o", "--output", "output_dir", default=".", help="Output directory")
@click.option("--no-wait", is_flag=True, help="Don't wait for result")
@click.pass_context
def image_upscale(ctx, image_path, model, scale, output_dir, no_wait):
    """Upscale an image.

    Example: novita image upscale photo.jpg --scale 2
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)
    request = {"model_name": model, "image_base64": img_b64, "scale_factor": scale}

    try:
        task_id = client.upscale(request)
        if no_wait:
            output_json({"task_id": task_id}) if ctx.obj.get("json") else output_text(f"Task ID: {task_id}")
            return

        output_text(f"Task submitted: {task_id}")
        result = client.poll_task(task_id, progress_callback=output_progress if not ctx.obj.get("json") else None)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            for i, img in enumerate(result.get("images", [])):
                url = img.get("image_url", "")
                ext = img.get("image_type", "png")
                out_path = os.path.join(output_dir, f"novita_upscale_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("remove-bg")
@click.argument("image_path")
@click.option("-o", "--output", "output_path", default=None, help="Output file path")
@click.option("--format", "img_format", default="png", type=click.Choice(["png", "webp", "jpeg"]))
@click.pass_context
def image_remove_bg(ctx, image_path, output_path, img_format):
    """Remove background from an image (sync).

    Example: novita image remove-bg photo.jpg -o clean.png
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)
    extra = {"response_image_type": img_format}

    try:
        result = client.remove_background(img_b64, extra)
        if ctx.obj.get("json"):
            output_json({"image_type": result.get("image_type"), "size": len(result.get("image_file", ""))})
        else:
            out = output_path or f"nobg_{Path(image_path).stem}.{img_format}"
            img_data = base64.b64decode(result["image_file"])
            with open(out, "wb") as f:
                f.write(img_data)
            output_text(f"Saved: {out}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("img2img")
@click.argument("image_path")
@click.argument("prompt")
@click.option("-m", "--model", default="sd_xl_base_1.0.safetensors", help="Model name")
@click.option("-W", "--width", default=1024, type=int, help="Width")
@click.option("-H", "--height", default=1024, type=int, help="Height")
@click.option("-n", "--num", default=1, type=int, help="Number of images")
@click.option("--steps", default=20, type=int, help="Steps")
@click.option("--cfg", "guidance_scale", default=7.5, type=float, help="Guidance scale")
@click.option("--sampler", default="Euler a", help="Sampler")
@click.option("--strength", default=0.7, type=float, help="Denoising strength (0-1)")
@click.option("--negative", default="", help="Negative prompt")
@click.option("--seed", default=-1, type=int, help="Seed")
@click.option("-o", "--output", "output_dir", default=".", help="Output directory")
@click.option("--no-wait", is_flag=True)
@click.pass_context
def image_img2img(ctx, image_path, prompt, model, width, height, num, steps,
                  guidance_scale, sampler, strength, negative, seed, output_dir, no_wait):
    """Generate images from an existing image + prompt (img2img).

    Example: novita image img2img photo.jpg "make it watercolor" --strength 0.5
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)
    request = {
        "model_name": model, "image_base64": img_b64, "prompt": prompt,
        "width": width, "height": height, "image_num": num,
        "steps": steps, "guidance_scale": guidance_scale,
        "sampler_name": sampler, "strength": strength, "seed": seed,
    }
    if negative:
        request["negative_prompt"] = negative

    try:
        task_id = client.img2img(request)
        if no_wait:
            output_json({"task_id": task_id}) if ctx.obj.get("json") else output_text(f"Task ID: {task_id}")
            return
        output_text(f"Task submitted: {task_id}")
        result = client.poll_task(task_id, progress_callback=output_progress if not ctx.obj.get("json") else None)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            os.makedirs(output_dir, exist_ok=True)
            for i, img in enumerate(result.get("images", [])):
                url = img.get("image_url", "")
                ext = img.get("image_type", "png")
                out_path = os.path.join(output_dir, f"novita_i2i_{task_id[:8]}_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("inpainting")
@click.argument("image_path")
@click.argument("mask_path")
@click.argument("prompt")
@click.option("-m", "--model", default="sd_xl_base_1.0.safetensors", help="Model name")
@click.option("-n", "--num", default=1, type=int, help="Number of images")
@click.option("--steps", default=20, type=int, help="Steps")
@click.option("--cfg", "guidance_scale", default=7.5, type=float, help="Guidance scale")
@click.option("--sampler", default="Euler a", help="Sampler")
@click.option("--strength", default=0.7, type=float, help="Strength (0-1)")
@click.option("--seed", default=-1, type=int, help="Seed")
@click.option("-o", "--output", "output_dir", default=".", help="Output directory")
@click.option("--no-wait", is_flag=True)
@click.pass_context
def image_inpainting(ctx, image_path, mask_path, prompt, model, num, steps,
                     guidance_scale, sampler, strength, seed, output_dir, no_wait):
    """Inpaint masked region of an image.

    Example: novita image inpainting photo.jpg mask.png "a red flower"
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)
    mask_b64 = read_image_file(mask_path)
    request = {
        "model_name": model, "image_base64": img_b64, "mask_image_base64": mask_b64,
        "prompt": prompt, "image_num": num, "steps": steps,
        "guidance_scale": guidance_scale, "sampler_name": sampler,
        "strength": strength, "seed": seed,
    }

    try:
        task_id = client.inpainting(request)
        if no_wait:
            output_json({"task_id": task_id}) if ctx.obj.get("json") else output_text(f"Task ID: {task_id}")
            return
        output_text(f"Task submitted: {task_id}")
        result = client.poll_task(task_id, progress_callback=output_progress if not ctx.obj.get("json") else None)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            os.makedirs(output_dir, exist_ok=True)
            for i, img in enumerate(result.get("images", [])):
                url = img.get("image_url", "")
                ext = img.get("image_type", "png")
                out_path = os.path.join(output_dir, f"novita_inpaint_{task_id[:8]}_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("replace-bg")
@click.argument("image_path")
@click.argument("prompt")
@click.option("-o", "--output", "output_path", default=None, help="Output file path")
@click.option("--no-wait", is_flag=True)
@click.pass_context
def image_replace_bg(ctx, image_path, prompt, output_path, no_wait):
    """Replace background of an image (async).

    Example: novita image replace-bg photo.jpg "a beach sunset"
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)
    try:
        task_id = client.replace_background(img_b64, prompt)
        if no_wait:
            output_json({"task_id": task_id}) if ctx.obj.get("json") else output_text(f"Task ID: {task_id}")
            return
        output_text(f"Task submitted: {task_id}")
        result = client.poll_task(task_id, progress_callback=output_progress if not ctx.obj.get("json") else None)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            for i, img in enumerate(result.get("images", [])):
                url = img.get("image_url", "")
                ext = img.get("image_type", "png")
                out = output_path or f"novita_replbg_{task_id[:8]}_{i}.{ext}"
                download_url(url, out)
                output_text(f"Saved: {out}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("reimagine")
@click.argument("image_path")
@click.option("-o", "--output", "output_path", default=None, help="Output file path")
@click.pass_context
def image_reimagine(ctx, image_path, output_path):
    """Reimagine an image (sync).

    Example: novita image reimagine photo.jpg -o reimagined.png
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)
    try:
        result = client.reimagine(img_b64)
        if ctx.obj.get("json"):
            output_json({"image_type": result.get("image_type"), "size": len(result.get("image_file", ""))})
        else:
            out = output_path or f"reimagine_{Path(image_path).stem}.png"
            img_data = base64.b64decode(result["image_file"])
            with open(out, "wb") as f:
                f.write(img_data)
            output_text(f"Saved: {out}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("cleanup")
@click.argument("image_path")
@click.argument("mask_path")
@click.option("-o", "--output", "output_path", default=None, help="Output file path")
@click.pass_context
def image_cleanup(ctx, image_path, mask_path, output_path):
    """Clean up / erase masked region of an image (sync).

    Example: novita image cleanup photo.jpg mask.png -o cleaned.png
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)
    mask_b64 = read_image_file(mask_path)
    try:
        result = client.cleanup(img_b64, mask_b64)
        if ctx.obj.get("json"):
            output_json({"image_type": result.get("image_type"), "size": len(result.get("image_file", ""))})
        else:
            out = output_path or f"cleanup_{Path(image_path).stem}.png"
            img_data = base64.b64decode(result["image_file"])
            with open(out, "wb") as f:
                f.write(img_data)
            output_text(f"Saved: {out}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("outpainting")
@click.argument("image_path")
@click.argument("prompt")
@click.option("-W", "--width", default=1024, type=int, help="Target width (max 4096)")
@click.option("-H", "--height", default=1024, type=int, help="Target height (max 4096)")
@click.option("--center-x", default=512, type=int, help="Image center X position")
@click.option("--center-y", default=512, type=int, help="Image center Y position")
@click.option("-o", "--output", "output_path", default=None, help="Output file path")
@click.pass_context
def image_outpainting(ctx, image_path, prompt, width, height, center_x, center_y, output_path):
    """Extend an image beyond its borders (sync).

    Example: novita image outpainting photo.jpg "forest landscape" -W 1536 -H 1024
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)
    try:
        result = client.outpainting(img_b64, prompt, width, height, center_x, center_y)
        if ctx.obj.get("json"):
            output_json({"image_type": result.get("image_type"), "size": len(result.get("image_file", ""))})
        else:
            out = output_path or f"outpaint_{Path(image_path).stem}.png"
            img_data = base64.b64decode(result["image_file"])
            with open(out, "wb") as f:
                f.write(img_data)
            output_text(f"Saved: {out}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("remove-text")
@click.argument("image_path")
@click.option("-o", "--output", "output_path", default=None, help="Output file path")
@click.pass_context
def image_remove_text(ctx, image_path, output_path):
    """Remove text from an image (sync).

    Example: novita image remove-text photo.jpg -o clean.png
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)
    try:
        result = client.remove_text(img_b64)
        if ctx.obj.get("json"):
            output_json({"image_type": result.get("image_type"), "size": len(result.get("image_file", ""))})
        else:
            out = output_path or f"notext_{Path(image_path).stem}.png"
            img_data = base64.b64decode(result["image_file"])
            with open(out, "wb") as f:
                f.write(img_data)
            output_text(f"Saved: {out}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("to-prompt")
@click.argument("image_path")
@click.pass_context
def image_to_prompt(ctx, image_path):
    """Generate a text prompt describing an image (sync).

    Example: novita image to-prompt photo.jpg
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)
    try:
        result = client.img2prompt(img_b64)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(result.get("prompt", ""))
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@image.command("merge-face")
@click.argument("face_image_path")
@click.argument("target_image_path")
@click.option("-o", "--output", "output_path", default=None, help="Output file path")
@click.pass_context
def image_merge_face(ctx, face_image_path, target_image_path, output_path):
    """Merge a face onto another image (sync).

    Example: novita image merge-face face.jpg target.jpg -o merged.png
    """
    client = get_client(ctx)
    face_b64 = read_image_file(face_image_path)
    target_b64 = read_image_file(target_image_path)
    try:
        result = client.merge_face(face_b64, target_b64)
        if ctx.obj.get("json"):
            output_json({"image_type": result.get("image_type"), "size": len(result.get("image_file", ""))})
        else:
            out = output_path or f"merged_{Path(target_image_path).stem}.png"
            img_data = base64.b64decode(result["image_file"])
            with open(out, "wb") as f:
                f.write(img_data)
            output_text(f"Saved: {out}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Video ───────────────────────────────────────────────────────────────────

@cli.group()
def video():
    """Video generation commands."""
    pass


@video.command("generate")
@click.argument("prompt")
@click.option("-m", "--model", default="darkSushiMixMix_225D_64380.safetensors", help="Model")
@click.option("-W", "--width", default=512, type=int, help="Width")
@click.option("-H", "--height", default=512, type=int, help="Height")
@click.option("--steps", default=20, type=int, help="Steps")
@click.option("--frames", default=32, type=int, help="Number of frames")
@click.option("--seed", default=-1, type=int, help="Seed")
@click.option("--negative", default="", help="Negative prompt")
@click.option("-o", "--output", "output_dir", default=".", help="Output directory")
@click.option("--no-wait", is_flag=True, help="Don't wait for result")
@click.pass_context
def video_generate(ctx, prompt, model, width, height, steps, frames, seed, negative, output_dir, no_wait):
    """Generate video from text.

    Example: novita video generate "a girl walking in snow" --frames 32
    """
    client = get_client(ctx)
    request = {
        "model_name": model,
        "height": height,
        "width": width,
        "steps": steps,
        "seed": seed,
        "prompts": [{"frames": frames, "prompt": prompt}],
    }
    if negative:
        request["negative_prompt"] = negative

    try:
        task_id = client.txt2video(request)
        if no_wait:
            output_json({"task_id": task_id}) if ctx.obj.get("json") else output_text(f"Task ID: {task_id}")
            return

        output_text(f"Task submitted: {task_id}")
        result = client.poll_task(task_id, progress_callback=output_progress if not ctx.obj.get("json") else None)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            for i, vid in enumerate(result.get("videos", [])):
                url = vid.get("video_url", "")
                ext = vid.get("video_type", "mp4")
                out_path = os.path.join(output_dir, f"novita_video_{task_id[:8]}_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@video.command("from-image")
@click.argument("image_path")
@click.option("-m", "--model", default="SVD-XT", type=click.Choice(["SVD", "SVD-XT"]))
@click.option("--frames", default=25, type=int, help="Frames (14 for SVD, 25 for SVD-XT)")
@click.option("--steps", default=20, type=int, help="Steps (1-50)")
@click.option("--seed", default=-1, type=int, help="Seed")
@click.option("-o", "--output", "output_dir", default=".", help="Output directory")
@click.option("--no-wait", is_flag=True)
@click.pass_context
def video_from_image(ctx, image_path, model, frames, steps, seed, output_dir, no_wait):
    """Generate video from an image.

    Example: novita video from-image photo.jpg --model SVD-XT
    """
    client = get_client(ctx)
    img_b64 = read_image_file(image_path)

    try:
        task_id = client.img2video(
            model_name=model, image_file=img_b64, frames_num=frames,
            frames_per_second=6, image_file_resize_mode="CROP_TO_ASPECT_RATIO",
            steps=steps, seed=seed,
        )
        if no_wait:
            output_json({"task_id": task_id}) if ctx.obj.get("json") else output_text(f"Task ID: {task_id}")
            return

        output_text(f"Task submitted: {task_id}")
        result = client.poll_task(task_id, progress_callback=output_progress if not ctx.obj.get("json") else None)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            for i, vid in enumerate(result.get("videos", [])):
                url = vid.get("video_url", "")
                ext = vid.get("video_type", "mp4")
                out_path = os.path.join(output_dir, f"novita_i2v_{task_id[:8]}_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@video.command("hunyuan")
@click.argument("prompt")
@click.option("-W", "--width", default=1280, type=int, help="Width (720 or 1280)")
@click.option("-H", "--height", default=720, type=int, help="Height (720 or 1280)")
@click.option("--steps", default=10, type=int, help="Steps (2-30)")
@click.option("--frames", default=85, type=int, help="Frames")
@click.option("--seed", default=-1, type=int, help="Seed")
@click.option("-o", "--output", "output_dir", default=".", help="Output directory")
@click.option("--no-wait", is_flag=True)
@click.pass_context
def video_hunyuan(ctx, prompt, width, height, steps, frames, seed, output_dir, no_wait):
    """Generate video with Hunyuan Video Fast.

    Example: novita video hunyuan "a cat playing piano"
    """
    client = get_client(ctx)
    try:
        task_id = client.hunyuan_video(
            model_name="hunyuan-video-fast", prompt=prompt,
            width=width, height=height, steps=steps, frames=frames, seed=seed,
        )
        if no_wait:
            output_json({"task_id": task_id}) if ctx.obj.get("json") else output_text(f"Task ID: {task_id}")
            return

        output_text(f"Task submitted: {task_id}")
        result = client.poll_task(task_id, progress_callback=output_progress if not ctx.obj.get("json") else None)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            for i, vid in enumerate(result.get("videos", [])):
                url = vid.get("video_url", "")
                ext = vid.get("video_type", "mp4")
                out_path = os.path.join(output_dir, f"novita_hunyuan_{task_id[:8]}_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Audio ───────────────────────────────────────────────────────────────────

@cli.group()
def audio():
    """Audio generation and transcription commands."""
    pass


@audio.command("tts")
@click.argument("text")
@click.option("--voice", default="Wise_Woman", help="Voice ID")
@click.option("--speed", default=1.0, type=float, help="Speed (0.5-2)")
@click.option("--emotion", default=None, type=click.Choice(["happy", "sad", "angry", "fearful", "disgusted", "surprised", "neutral"]))
@click.option("--format", "audio_format", default="mp3", type=click.Choice(["mp3", "wav", "flac", "pcm"]))
@click.option("-o", "--output", "output_path", default=None, help="Output file")
@click.pass_context
def audio_tts(ctx, text, voice, speed, emotion, audio_format, output_path):
    """Text-to-speech with MiniMax Speech-02-HD.

    Example: novita audio tts "Hello world" --voice Calm_Woman -o hello.mp3
    """
    client = get_client(ctx)
    kwargs = {
        "text": text,
        "voice_setting": {"voice_id": voice, "speed": speed},
        "audio_setting": {"format": audio_format},
        "output_format": "url",
    }
    if emotion:
        kwargs["voice_setting"]["emotion"] = emotion

    try:
        result = client.minimax_tts(**kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            audio_url = result.get("audio", "")
            if audio_url.startswith("http"):
                out = output_path or f"novita_tts.{audio_format}"
                download_url(audio_url, out)
                output_text(f"Saved: {out}")
            else:
                output_text(f"Audio data returned ({len(audio_url)} chars)")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@audio.command("asr")
@click.argument("audio_source")
@click.option("--prompt", "context_prompt", default=None, help="Context for transcription")
@click.pass_context
def audio_asr(ctx, audio_source, context_prompt):
    """Speech-to-text with GLM ASR.

    AUDIO_SOURCE can be a URL or local file path.

    Example: novita audio asr recording.wav
    """
    client = get_client(ctx)
    if os.path.isfile(audio_source):
        ext = Path(audio_source).suffix.lstrip(".")
        mime = {"mp3": "audio/mp3", "wav": "audio/wav", "flac": "audio/flac"}.get(ext, f"audio/{ext}")
        with open(audio_source, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        file_data = f"data:{mime};base64,{b64}"
    else:
        file_data = audio_source  # assume URL

    kwargs = {"file": file_data}
    if context_prompt:
        kwargs["prompt"] = context_prompt

    try:
        result = client.glm_asr(**kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(result.get("text", ""))
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@audio.command("glm-tts")
@click.argument("text")
@click.option("--voice", default="tongtong", type=click.Choice(["tongtong", "chuichui", "xiaochen", "jam", "kazi", "douji", "luodo"]))
@click.option("--speed", default=1.0, type=float, help="Speed (0.5-2)")
@click.option("--format", "audio_format", default="wav", type=click.Choice(["wav", "pcm"]))
@click.option("-o", "--output", "output_path", default=None, help="Output file")
@click.pass_context
def audio_glm_tts(ctx, text, voice, speed, audio_format, output_path):
    """Text-to-speech with GLM TTS.

    Example: novita audio glm-tts "Hello world" --voice jam -o hello.wav
    """
    client = get_client(ctx)
    kwargs = {"input": text, "voice": voice, "speed": speed, "response_format": audio_format}
    try:
        result = client.glm_tts(**kwargs)
        if "audio_data" in result:
            # Binary audio response
            if ctx.obj.get("json"):
                output_json({"content_type": result["content_type"], "size": len(result["audio_data"])})
            else:
                out = output_path or f"novita_glm_tts.{audio_format}"
                with open(out, "wb") as f:
                    f.write(result["audio_data"])
                output_text(f"Saved: {out}")
        elif ctx.obj.get("json"):
            output_json(result)
        else:
            audio_url = result.get("audio", {}).get("url", "") if isinstance(result.get("audio"), dict) else result.get("audio", "")
            if audio_url and audio_url.startswith("http"):
                out = output_path or f"novita_glm_tts.{audio_format}"
                download_url(audio_url, out)
                output_text(f"Saved: {out}")
            else:
                output_text(f"Audio data returned ({len(str(result))} chars)")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@audio.command("voice-clone")
@click.argument("audio_url")
@click.option("--text", default=None, help="Preview text (max 2000 chars)")
@click.option("--model", default="speech-02-hd", help="TTS model to use")
@click.option("--accuracy", default=None, type=float, help="Accuracy (0-1)")
@click.pass_context
def audio_voice_clone(ctx, audio_url, text, model, accuracy):
    """Clone a voice from audio (MiniMax).

    Example: novita audio voice-clone https://example.com/voice.mp3
    """
    client = get_client(ctx)
    kwargs = {}
    if text:
        kwargs["text"] = text
    if model:
        kwargs["model"] = model
    if accuracy is not None:
        kwargs["accuracy"] = accuracy
    try:
        result = client.voice_clone(audio_url, **kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Voice ID: {result.get('voice_id', '')}")
            if result.get("audio_url"):
                output_text(f"Preview:  {result['audio_url']}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Account ─────────────────────────────────────────────────────────────────

@cli.group()
def account():
    """Account and billing commands."""
    pass


@account.command("balance")
@click.pass_context
def account_balance(ctx):
    """Show account balance.

    Example: novita account balance
    """
    client = get_client(ctx)
    try:
        result = client.get_balance()
        if ctx.obj.get("json"):
            output_json(result)
        else:
            credit = result.get("credit_balance", 0)
            output_text(f"Credit Balance: {format_balance(str(credit))}")
            features = result.get("allow_features", [])
            if features:
                output_text(f"Features: {', '.join(features)}")
            trial = result.get("free_trial", {})
            if trial:
                output_text(f"Free Trial: {trial}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@account.command("billing")
@click.pass_context
def account_billing(ctx):
    """Show monthly billing info.

    Example: novita account billing
    """
    client = get_client(ctx)
    try:
        result = client.get_monthly_bill()
        if ctx.obj.get("json"):
            output_json(result)
        else:
            bills = result.get("data", [])
            if not bills:
                output_text("No billing data.")
            for bill in bills:
                output_text(f"Month: {bill.get('billingMonth', 'N/A')}")
                output_text(f"  Total: {format_balance(bill.get('totalAmount', '0'))}")
                output_text(f"  Status: {bill.get('status', 'N/A')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@account.command("usage-billing")
@click.pass_context
def account_usage_billing(ctx):
    """Show usage-based billing details.

    Example: novita account usage-billing
    """
    client = get_client(ctx)
    try:
        result = client.get_usage_billing()
        if ctx.obj.get("json"):
            output_json(result)
        else:
            bills = result.get("data", [])
            if not bills:
                output_text("No usage-based billing data.")
            for bill in bills:
                output_text(f"  Period: {bill.get('billingMonth', 'N/A')}")
                output_text(f"  Amount: {format_balance(bill.get('totalAmount', '0'))}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@account.command("fixed-billing")
@click.pass_context
def account_fixed_billing(ctx):
    """Show fixed-term billing details.

    Example: novita account fixed-billing
    """
    client = get_client(ctx)
    try:
        result = client.get_fixed_billing()
        if ctx.obj.get("json"):
            output_json(result)
        else:
            bills = result.get("data", [])
            if not bills:
                output_text("No fixed-term billing data.")
            for bill in bills:
                output_text(f"  Period: {bill.get('billingMonth', 'N/A')}")
                output_text(f"  Amount: {format_balance(bill.get('totalAmount', '0'))}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Task ────────────────────────────────────────────────────────────────────

@cli.group()
def task():
    """Manage async tasks."""
    pass


@task.command("status")
@click.argument("task_id")
@click.pass_context
def task_status(ctx, task_id):
    """Check async task status.

    Example: novita task status abc123-def456
    """
    client = get_client(ctx)
    try:
        result = client.get_task_result(task_id)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            t = result.get("task", {})
            output_text(f"Task:     {t.get('task_id', '')}")
            output_text(f"Type:     {t.get('task_type', '')}")
            output_text(f"Status:   {t.get('status', '')}")
            output_text(f"Progress: {t.get('progress_percent', 0)}%")
            if t.get("reason"):
                output_text(f"Reason:   {t['reason']}")
            for img in result.get("images", []):
                output_text(f"Image:    {img.get('image_url', '')}")
            for vid in result.get("videos", []):
                output_text(f"Video:    {vid.get('video_url', '')}")
            for aud in result.get("audios", []):
                output_text(f"Audio:    {aud.get('audio_url', '')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@task.command("wait")
@click.argument("task_id")
@click.option("--timeout", default=600, type=int, help="Timeout in seconds")
@click.option("-o", "--output", "output_dir", default=".", help="Output directory")
@click.pass_context
def task_wait(ctx, task_id, timeout, output_dir):
    """Wait for an async task and download results.

    Example: novita task wait abc123-def456 -o ./results
    """
    client = get_client(ctx)
    try:
        result = client.poll_task(
            task_id, timeout=timeout,
            progress_callback=output_progress if not ctx.obj.get("json") else None,
        )
        if ctx.obj.get("json"):
            output_json(result)
        else:
            os.makedirs(output_dir, exist_ok=True)
            for i, img in enumerate(result.get("images", [])):
                url = img.get("image_url", "")
                ext = img.get("image_type", "png")
                out_path = os.path.join(output_dir, f"task_{task_id[:8]}_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
            for i, vid in enumerate(result.get("videos", [])):
                url = vid.get("video_url", "")
                ext = vid.get("video_type", "mp4")
                out_path = os.path.join(output_dir, f"task_{task_id[:8]}_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
            for i, aud in enumerate(result.get("audios", [])):
                url = aud.get("audio_url", "")
                ext = aud.get("audio_type", "wav")
                out_path = os.path.join(output_dir, f"task_{task_id[:8]}_{i}.{ext}")
                download_url(url, out_path)
                output_text(f"Saved: {out_path}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Batch ───────────────────────────────────────────────────────────────────

@cli.group()
def batch():
    """Batch processing commands."""
    pass


@batch.command("create")
@click.argument("input_file_id")
@click.option("--endpoint", default="/v1/chat/completions", help="API endpoint")
@click.pass_context
def batch_create(ctx, input_file_id, endpoint):
    """Create a batch job.

    Example: novita batch create file-abc123
    """
    client = get_client(ctx)
    try:
        result = client.create_batch(
            input_file_id=input_file_id, endpoint=endpoint, completion_window="48h",
        )
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Batch ID: {result.get('id', '')}")
            output_text(f"Status:   {result.get('status', '')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@batch.command("list")
@click.pass_context
def batch_list(ctx):
    """List all batches.

    Example: novita batch list
    """
    client = get_client(ctx)
    try:
        result = client.list_batches()
        if ctx.obj.get("json"):
            output_json(result)
        else:
            for b in result.get("data") or []:
                output_text(f"{b.get('id', '')}  {b.get('status', '')}  {b.get('endpoint', '')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@batch.command("get")
@click.argument("batch_id")
@click.pass_context
def batch_get(ctx, batch_id):
    """Get batch details.

    Example: novita batch get batch-abc123
    """
    client = get_client(ctx)
    try:
        result = client.retrieve_batch(batch_id)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            for k, v in result.items():
                output_text(f"  {k}: {v}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@batch.command("cancel")
@click.argument("batch_id")
@click.pass_context
def batch_cancel(ctx, batch_id):
    """Cancel a batch job.

    Example: novita batch cancel batch-abc123
    """
    client = get_client(ctx)
    try:
        result = client.cancel_batch(batch_id)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Cancelled: {result.get('id', batch_id)}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Files ───────────────────────────────────────────────────────────────────

@cli.group()
def files():
    """File management for batch processing."""
    pass


@files.command("upload")
@click.argument("file_path")
@click.pass_context
def files_upload(ctx, file_path):
    """Upload a JSONL file for batch processing.

    Example: novita files upload batch_input.jsonl
    """
    client = get_client(ctx)
    try:
        result = client.upload_batch_file(file_path)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"File ID: {result.get('id', '')}")
            output_text(f"Status:  {result.get('status', '')}")
            output_text(f"Size:    {result.get('bytes', 0)} bytes")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@files.command("list")
@click.pass_context
def files_list(ctx):
    """List uploaded files.

    Example: novita files list
    """
    client = get_client(ctx)
    try:
        result = client.list_files()
        if ctx.obj.get("json"):
            output_json(result)
        else:
            data = result.get("data", [])
            if not data:
                output_text("No files found.")
                return
            rows = []
            for f in data:
                rows.append([
                    f.get("id", ""),
                    f.get("filename", ""),
                    str(f.get("bytes", 0)),
                    f.get("purpose", ""),
                    f.get("status", ""),
                ])
            output_text(format_table(rows, ["ID", "Filename", "Bytes", "Purpose", "Status"]))
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@files.command("get")
@click.argument("file_id")
@click.pass_context
def files_get(ctx, file_id):
    """Get file details.

    Example: novita files get file-abc123
    """
    client = get_client(ctx)
    try:
        result = client.retrieve_file(file_id)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            for k, v in result.items():
                output_text(f"  {k}: {v}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@files.command("delete")
@click.argument("file_id")
@click.pass_context
def files_delete(ctx, file_id):
    """Delete an uploaded file.

    Example: novita files delete file-abc123
    """
    client = get_client(ctx)
    try:
        result = client.delete_file(file_id)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Deleted: {file_id}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@files.command("content")
@click.argument("file_id")
@click.option("-o", "--output", "output_path", default=None, help="Save to file")
@click.pass_context
def files_content(ctx, file_id, output_path):
    """Retrieve file content.

    Example: novita files content file-abc123
    """
    client = get_client(ctx)
    try:
        content = client.retrieve_file_content(file_id)
        if output_path:
            with open(output_path, "w") as f:
                f.write(content)
            output_text(f"Saved: {output_path}")
        else:
            output_text(content)
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── GPU Instances ───────────────────────────────────────────────────────────

@cli.group()
def gpu():
    """GPU instance management commands."""
    pass


@gpu.command("list")
@click.option("--page-size", default=20, type=int, help="Items per page")
@click.option("--page", default=0, type=int, help="Page number")
@click.option("--name", default=None, help="Filter by instance name")
@click.option("--status", default=None, help="Filter by status")
@click.pass_context
def gpu_list(ctx, page_size, page, name, status):
    """List GPU instances.

    Example: novita gpu list --status running
    """
    client = get_client(ctx)
    kwargs = {}
    if name:
        kwargs["name"] = name
    if status:
        kwargs["status"] = status
    try:
        result = client.gpu_list_instances(page_size=page_size, page_num=page, **kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            instances = result.get("instances", [])
            if not instances:
                output_text("No instances found.")
                return
            rows = []
            for inst in instances:
                rows.append([
                    inst.get("id", "")[:12],
                    inst.get("name", ""),
                    inst.get("status", ""),
                    inst.get("productName", ""),
                    str(inst.get("gpuNum", "")),
                    inst.get("billingMode", ""),
                ])
            output_text(format_table(rows, ["ID", "Name", "Status", "Product", "GPUs", "Billing"]))
            output_text(f"Total: {result.get('total', 0)}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("create")
@click.option("--product-id", required=True, help="GPU product ID")
@click.option("--gpu-num", default=1, type=int, help="Number of GPUs (1-8)")
@click.option("--image", required=True, help="Container image URL")
@click.option("--name", default=None, help="Instance name")
@click.option("--rootfs", default=40, type=int, help="Root filesystem size in GB")
@click.option("--ports", default=None, help="Ports, e.g. '80/http,3306/tcp'")
@click.option("--command", "cmd", default=None, help="Startup command")
@click.option("--billing", default="onDemand", type=click.Choice(["onDemand", "monthly", "spot"]))
@click.option("--kind", default="gpu", type=click.Choice(["gpu", "cpu"]))
@click.option("--env", multiple=True, help="Environment vars as KEY=VALUE")
@click.pass_context
def gpu_create(ctx, product_id, gpu_num, image, name, rootfs, ports, cmd, billing, kind, env):
    """Create a GPU instance.

    Example: novita gpu create --product-id xxx --image pytorch/pytorch:latest --gpu-num 1
    """
    client = get_client(ctx)
    kwargs = {
        "productId": product_id,
        "gpuNum": gpu_num,
        "imageUrl": image,
        "rootfsSize": rootfs,
        "kind": kind,
        "billingMode": billing,
    }
    if name:
        kwargs["name"] = name
    if ports:
        kwargs["ports"] = ports
    if cmd:
        kwargs["command"] = cmd
    if env:
        kwargs["envs"] = [{"key": e.split("=", 1)[0], "value": e.split("=", 1)[1]} for e in env if "=" in e]

    try:
        result = client.gpu_create_instance(**kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Instance created: {result.get('id', '')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("get")
@click.argument("instance_id")
@click.pass_context
def gpu_get(ctx, instance_id):
    """Get GPU instance details.

    Example: novita gpu get abc123
    """
    client = get_client(ctx)
    try:
        result = client.gpu_get_instance(instance_id)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            for k in ["id", "name", "status", "imageUrl", "cpuNum", "memory", "gpuNum", "billingMode"]:
                if k in result:
                    output_text(f"  {k}: {result[k]}")
            ports = result.get("portMappings", [])
            if ports:
                output_text("  Ports:")
                for p in ports:
                    output_text(f"    {p.get('port', '')} -> {p.get('endpoint', '')} ({p.get('protocol', '')})")
            ssh = result.get("connectComponentSSH", {})
            if ssh:
                output_text(f"  SSH: {ssh}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("start")
@click.argument("instance_id")
@click.pass_context
def gpu_start(ctx, instance_id):
    """Start a GPU instance.

    Example: novita gpu start abc123
    """
    client = get_client(ctx)
    try:
        client.gpu_start_instance(instance_id)
        output_text(f"Instance {instance_id} starting.")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("stop")
@click.argument("instance_id")
@click.pass_context
def gpu_stop(ctx, instance_id):
    """Stop a GPU instance.

    Example: novita gpu stop abc123
    """
    client = get_client(ctx)
    try:
        client.gpu_stop_instance(instance_id)
        output_text(f"Instance {instance_id} stopping.")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("delete")
@click.argument("instance_id")
@click.pass_context
def gpu_delete(ctx, instance_id):
    """Delete a GPU instance.

    Example: novita gpu delete abc123
    """
    client = get_client(ctx)
    try:
        client.gpu_delete_instance(instance_id)
        output_text(f"Instance {instance_id} deleted.")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("restart")
@click.argument("instance_id")
@click.pass_context
def gpu_restart(ctx, instance_id):
    """Restart a GPU instance.

    Example: novita gpu restart abc123
    """
    client = get_client(ctx)
    try:
        client.gpu_restart_instance(instance_id)
        output_text(f"Instance {instance_id} restarting.")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("clusters")
@click.pass_context
def gpu_clusters(ctx):
    """List available clusters/data centers.

    Example: novita gpu clusters
    """
    client = get_client(ctx)
    try:
        result = client.gpu_list_clusters()
        if ctx.obj.get("json"):
            output_json(result)
        else:
            clusters = result.get("data", result.get("clusters", []))
            if not clusters:
                output_text("No clusters found.")
                return
            for c in clusters:
                output_text(f"  {c.get('id', '')}  {c.get('name', '')}  {c.get('region', '')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("products")
@click.option("--gpu-num", default=None, type=int, help="Filter by GPU count")
@click.option("--name", "product_name", default=None, help="Filter by product name")
@click.option("--billing", default=None, help="Filter by billing method")
@click.pass_context
def gpu_products(ctx, gpu_num, product_name, billing):
    """List available GPU products.

    Example: novita gpu products --gpu-num 1
    """
    client = get_client(ctx)
    kwargs = {}
    if gpu_num is not None:
        kwargs["gpuNum"] = gpu_num
    if product_name:
        kwargs["productName"] = product_name
    if billing:
        kwargs["billingMethod"] = billing
    try:
        result = client.gpu_list_products(**kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            products = result.get("data", [])
            if not products:
                output_text("No products found.")
                return
            rows = []
            for p in products:
                rows.append([
                    p.get("id", "")[:16],
                    p.get("name", ""),
                    str(p.get("cpuPerGpu", "")),
                    str(p.get("memoryPerGpu", "")),
                    str(p.get("price", "")),
                    "Yes" if p.get("availableDeploy") else "No",
                ])
            output_text(format_table(rows, ["ID", "Name", "CPU/GPU", "Mem/GPU", "Price", "Available"]))
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("cpu-products")
@click.option("--name", "product_name", default=None, help="Filter by name")
@click.pass_context
def gpu_cpu_products(ctx, product_name):
    """List available CPU products.

    Example: novita gpu cpu-products
    """
    client = get_client(ctx)
    kwargs = {}
    if product_name:
        kwargs["productName"] = product_name
    try:
        result = client.gpu_list_cpu_products(**kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_json(result)
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("metrics")
@click.argument("instance_id")
@click.option("--interval", default=15, type=int, help="Granularity in seconds")
@click.pass_context
def gpu_metrics(ctx, instance_id, interval):
    """Get GPU instance metrics.

    Example: novita gpu metrics abc123
    """
    client = get_client(ctx)
    try:
        result = client.gpu_get_metrics(instance_id, interval=interval)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            cpu = result.get("cpuUtilization", [])
            mem = result.get("memUtilization", [])
            gpu_util = result.get("gpuUtilization", {})
            if cpu:
                latest = cpu[-1] if cpu else {}
                output_text(f"CPU Utilization: {latest.get('value', 'N/A')}%")
            if mem:
                latest = mem[-1] if mem else {}
                output_text(f"Memory Utilization: {latest.get('value', 'N/A')}%")
            if gpu_util:
                avg = gpu_util.get("avg", [])
                if avg:
                    latest = avg[-1] if avg else {}
                    output_text(f"GPU Utilization: {latest.get('value', 'N/A')}%")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@gpu.command("edit")
@click.argument("instance_id")
@click.option("--ports", default=None, help="New ports config as JSON array")
@click.option("--expand-disk", default=None, type=int, help="Expand root disk by GB")
@click.pass_context
def gpu_edit(ctx, instance_id, ports, expand_disk):
    """Edit a GPU instance (ports, disk).

    Example: novita gpu edit abc123 --expand-disk 50
    """
    client = get_client(ctx)
    kwargs = {}
    if ports:
        kwargs["ports"] = json.loads(ports)
    if expand_disk:
        kwargs["expandRootDisk"] = expand_disk
    try:
        result = client.gpu_edit_instance(instance_id, **kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Instance {instance_id} updated.")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── GPU Storage ─────────────────────────────────────────────────────────────

@cli.group()
def storage():
    """Network storage management for GPU instances."""
    pass


@storage.command("list")
@click.pass_context
def storage_list(ctx):
    """List network storage volumes.

    Example: novita storage list
    """
    client = get_client(ctx)
    try:
        result = client.gpu_list_storage()
        if ctx.obj.get("json"):
            output_json(result)
        else:
            items = result.get("data", result.get("networkStorages", []))
            if not items:
                output_text("No storage volumes found.")
                return
            for s in items:
                output_text(f"  {s.get('id', '')}  {s.get('storageName', '')}  {s.get('storageSize', '')}GB  {s.get('clusterId', '')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@storage.command("create")
@click.option("--cluster-id", required=True, help="Cluster ID")
@click.option("--name", required=True, help="Storage name")
@click.option("--size", required=True, type=int, help="Size in GB")
@click.pass_context
def storage_create(ctx, cluster_id, name, size):
    """Create a network storage volume.

    Example: novita storage create --cluster-id cl-xxx --name mydata --size 100
    """
    client = get_client(ctx)
    try:
        result = client.gpu_create_storage(cluster_id, name, size)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Storage created: {result.get('id', '')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@storage.command("delete")
@click.argument("storage_id")
@click.pass_context
def storage_delete(ctx, storage_id):
    """Delete a network storage volume.

    Example: novita storage delete stor-abc123
    """
    client = get_client(ctx)
    try:
        client.gpu_delete_storage(storage_id)
        output_text(f"Storage {storage_id} deleted.")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── GPU Templates ───────────────────────────────────────────────────────────

@cli.group()
def template():
    """GPU instance template management."""
    pass


@template.command("list")
@click.option("--channel", default="private", type=click.Choice(["official", "community", "private"]))
@click.option("--name", default=None, help="Filter by name")
@click.option("--page-size", default=20, type=int)
@click.option("--page", default=0, type=int)
@click.pass_context
def template_list(ctx, channel, name, page_size, page):
    """List templates.

    Example: novita template list --channel official
    """
    client = get_client(ctx)
    is_my = channel == "private"
    kwargs = {}
    if name:
        kwargs["name"] = name
    try:
        result = client.gpu_list_templates(channel=channel, is_my_community=is_my,
                                           page_size=page_size, page_num=page, **kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            templates = result.get("template", [])
            if not templates:
                output_text("No templates found.")
                return
            rows = []
            for t in templates:
                rows.append([
                    t.get("Id", "")[:12],
                    t.get("name", ""),
                    t.get("image", ""),
                    str(t.get("rootfsSize", "")),
                ])
            output_text(format_table(rows, ["ID", "Name", "Image", "RootFS"]))
            output_text(f"Total: {result.get('total', 0)}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@template.command("get")
@click.argument("template_id")
@click.pass_context
def template_get(ctx, template_id):
    """Get template details.

    Example: novita template get abc123
    """
    client = get_client(ctx)
    try:
        result = client.gpu_get_template(template_id)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            for k in ["Id", "name", "image", "rootfsSize", "startCommand", "channel", "minCudaVersion"]:
                val = result.get(k)
                if val:
                    output_text(f"  {k}: {val}")
            envs = result.get("envs", [])
            if envs:
                output_text("  Envs:")
                for e in envs:
                    output_text(f"    {e.get('key', '')}={e.get('value', '')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@template.command("create")
@click.option("--name", required=True, help="Template name")
@click.option("--image", required=True, help="Docker image URL")
@click.option("--rootfs", default=40, type=int, help="Root filesystem size GB")
@click.option("--command", "cmd", default=None, help="Start command")
@click.option("--cuda", default=None, help="Min CUDA version")
@click.option("--env", multiple=True, help="Environment vars as KEY=VALUE")
@click.pass_context
def template_create(ctx, name, image, rootfs, cmd, cuda, env):
    """Create a template.

    Example: novita template create --name mytempl --image pytorch/pytorch:latest
    """
    client = get_client(ctx)
    tmpl = {
        "name": name,
        "type": "instance",
        "channel": "private",
        "image": image,
        "rootfsSize": rootfs,
    }
    if cmd:
        tmpl["startCommand"] = cmd
    if cuda:
        tmpl["minCudaVersion"] = cuda
    if env:
        tmpl["envs"] = [{"key": e.split("=", 1)[0], "value": e.split("=", 1)[1]} for e in env if "=" in e]

    try:
        result = client.gpu_create_template(tmpl)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Template created: {result.get('templateId', '')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@template.command("edit")
@click.argument("template_id")
@click.option("--name", default=None, help="New template name")
@click.option("--image", default=None, help="New Docker image URL")
@click.option("--rootfs", default=None, type=int, help="Root filesystem size GB")
@click.option("--command", "cmd", default=None, help="Start command")
@click.pass_context
def template_edit(ctx, template_id, name, image, rootfs, cmd):
    """Edit a template.

    Example: novita template edit abc123 --name "new-name"
    """
    client = get_client(ctx)
    try:
        current = client.gpu_get_template(template_id)
        tmpl = {"Id": template_id}
        tmpl["name"] = name if name else current.get("name", "")
        tmpl["image"] = image if image else current.get("image", "")
        tmpl["rootfsSize"] = rootfs if rootfs else current.get("rootfsSize", 40)
        tmpl["type"] = current.get("type", "instance")
        tmpl["channel"] = current.get("channel", "private")
        if cmd:
            tmpl["startCommand"] = cmd
        elif current.get("startCommand"):
            tmpl["startCommand"] = current["startCommand"]

        result = client.gpu_edit_template(tmpl)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Template {template_id} updated.")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@template.command("delete")
@click.argument("template_id")
@click.pass_context
def template_delete(ctx, template_id):
    """Delete a template.

    Example: novita template delete abc123
    """
    client = get_client(ctx)
    try:
        client.gpu_delete_template(template_id)
        output_text(f"Template {template_id} deleted.")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


# ── Serverless ──────────────────────────────────────────────────────────────

@cli.group()
def serverless():
    """Serverless GPU endpoint management."""
    pass


@serverless.command("list")
@click.option("--page-size", default=20, type=int)
@click.option("--page", default=0, type=int)
@click.pass_context
def serverless_list(ctx, page_size, page):
    """List serverless endpoints.

    Example: novita serverless list
    """
    client = get_client(ctx)
    try:
        result = client.serverless_list_endpoints(page_size=page_size, page_num=page)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            endpoints = result.get("endpoints", [])
            if not endpoints:
                output_text("No endpoints found.")
                return
            rows = []
            for ep in endpoints:
                state = ep.get("state", {}).get("state", "")
                rows.append([
                    ep.get("id", "")[:12],
                    ep.get("name", ""),
                    state,
                    ep.get("url", ""),
                ])
            output_text(format_table(rows, ["ID", "Name", "State", "URL"]))
            output_text(f"Total: {result.get('total', 0)}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@serverless.command("get")
@click.argument("endpoint_id")
@click.pass_context
def serverless_get(ctx, endpoint_id):
    """Get serverless endpoint details.

    Example: novita serverless get abc123
    """
    client = get_client(ctx)
    try:
        result = client.serverless_get_endpoint(endpoint_id)
        ep = result.get("endpoint", result)
        if ctx.obj.get("json"):
            output_json(ep)
        else:
            for k in ["id", "name", "appName", "url", "rootfsSize"]:
                if k in ep:
                    output_text(f"  {k}: {ep[k]}")
            state = ep.get("state", {})
            output_text(f"  state: {state.get('state', '')}")
            wc = ep.get("workerConfig", {})
            if wc:
                output_text(f"  workers: min={wc.get('minNum')}, max={wc.get('maxNum')}, gpu={wc.get('gpuNum')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@serverless.command("create")
@click.option("--name", default=None, help="Endpoint name")
@click.option("--image", required=True, help="Container image URL")
@click.option("--port", required=True, type=int, help="Service port")
@click.option("--product-id", required=True, help="GPU product ID")
@click.option("--gpu-num", default=1, type=int, help="GPUs per worker")
@click.option("--min-workers", default=0, type=int, help="Min workers")
@click.option("--max-workers", default=1, type=int, help="Max workers")
@click.option("--timeout", "free_timeout", default=300, type=int, help="Idle timeout (seconds)")
@click.option("--health-path", default="/health", help="Health check path")
@click.option("--command", "cmd", default=None, help="Container command")
@click.option("--env", multiple=True, help="Environment vars as KEY=VALUE")
@click.pass_context
def serverless_create(ctx, name, image, port, product_id, gpu_num, min_workers,
                      max_workers, free_timeout, health_path, cmd, env):
    """Create a serverless endpoint.

    Example: novita serverless create --image myimage:latest --port 8080 --product-id xxx
    """
    client = get_client(ctx)
    ep = {
        "rootfsSize": 100,
        "workerConfig": {
            "minNum": min_workers,
            "maxNum": max_workers,
            "freeTimeout": free_timeout,
            "maxConcurrent": 1,
            "gpuNum": gpu_num,
        },
        "ports": [{"port": str(port)}],
        "policy": {"type": "queue", "value": 1},
        "image": {"image": image},
        "volumeMounts": [{"type": "local", "size": 30, "mountPath": "/workspace"}],
        "healthy": {"path": health_path},
        "products": [{"id": product_id}],
    }
    if name:
        ep["name"] = name
    if cmd:
        ep["image"]["command"] = cmd
    if env:
        ep["envs"] = [{"key": e.split("=", 1)[0], "value": e.split("=", 1)[1]} for e in env if "=" in e]

    try:
        result = client.serverless_create_endpoint(ep)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Endpoint created: {result.get('id', '')}")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@serverless.command("update")
@click.argument("endpoint_id")
@click.option("--min-workers", default=None, type=int, help="Min workers")
@click.option("--max-workers", default=None, type=int, help="Max workers")
@click.option("--timeout", "free_timeout", default=None, type=int, help="Idle timeout")
@click.option("--image", default=None, help="Container image")
@click.pass_context
def serverless_update(ctx, endpoint_id, min_workers, max_workers, free_timeout, image):
    """Update a serverless endpoint.

    Example: novita serverless update abc123 --max-workers 3
    """
    client = get_client(ctx)
    # First get current config
    try:
        current = client.serverless_get_endpoint(endpoint_id)
        ep = current.get("endpoint", current)

        kwargs = {"id": endpoint_id}
        wc = ep.get("workerConfig", {})
        kwargs["workerConfig"] = {
            "minNum": min_workers if min_workers is not None else wc.get("minNum", 0),
            "maxNum": max_workers if max_workers is not None else wc.get("maxNum", 1),
            "freeTimeout": free_timeout if free_timeout is not None else wc.get("freeTimeout", 300),
            "maxConcurrent": wc.get("maxConcurrent", 1),
            "gpuNum": wc.get("gpuNum", 1),
        }
        kwargs["ports"] = ep.get("ports", [])
        kwargs["policy"] = ep.get("policy", {"type": "queue", "value": 1})
        img_obj = ep.get("image", {})
        if image:
            img_obj["image"] = image
        kwargs["image"] = img_obj

        result = client.serverless_update_endpoint(**kwargs)
        if ctx.obj.get("json"):
            output_json(result)
        else:
            output_text(f"Endpoint {endpoint_id} updated.")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


@serverless.command("delete")
@click.argument("endpoint_id")
@click.pass_context
def serverless_delete(ctx, endpoint_id):
    """Delete a serverless endpoint.

    Example: novita serverless delete abc123
    """
    client = get_client(ctx)
    try:
        client.serverless_delete_endpoint(endpoint_id)
        output_text(f"Endpoint {endpoint_id} deleted.")
    except NovitaError as e:
        output_error(str(e))
        sys.exit(1)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
