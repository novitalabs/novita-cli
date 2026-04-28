# Novita Platform Adapter

This skill uses only Novita through the `novita` CLI. Do not offer provider switching.

## Authentication

Novita requires an API key:

```bash
export NOVITA_API_KEY="sk_..."
```

If it is missing, guide the user to create a key at https://novita.ai/settings/key-management or pass `--api-key` on the command.

## Text To Image

Fast synchronous draft:

```bash
novita image flux "<polished prompt>" -W 1024 -H 1024 -n 1 --steps 4 -o ./outputs
```

Higher-control async generation:

```bash
novita image generate "<polished prompt>" -W 1024 -H 1024 -n 4 --steps 28 --cfg 7.5 -o ./outputs
```

For async control:

```bash
novita image generate "<polished prompt>" -W 1024 -H 1024 --no-wait --json-output
novita task wait <task_id> -o ./outputs --timeout 600
```

## Image Editing

| Need | Command |
|------|---------|
| Background removal | `novita image remove-bg input.png -o output.png` |
| Background replacement | `novita image replace-bg input.png "<new background>" -o ./outputs` |
| Style transfer / image-to-image | `novita image img2img input.png "<prompt>" --strength 0.5` |
| Inpainting | `novita image inpainting input.png mask.png "<prompt>"` |
| Cleanup masked area | `novita image cleanup input.png mask.png -o output.png` |
| Outpainting | `novita image outpainting input.png "<prompt>" -W 1536 -H 1024` |
| Remove text | `novita image remove-text input.png -o output.png` |
| Upscale | `novita image upscale input.png --scale 2` |
| Image prompt extraction | `novita image to-prompt input.png` |

## Recommended Workflow

1. Read the relevant template under `references/easy-image/templates/`.
2. Convert the user's short request into a polished English prompt.
3. Pick a size from `references/easy-image/model-selection.md`.
4. Run the matching `novita image ...` command.
5. For async commands, wait for the task and save results.

## Error Handling

| Error | Action |
|-------|--------|
| API key required | Ask the user to set `NOVITA_API_KEY` or pass `--api-key`. |
| Task timeout | Increase `--timeout` or rerun with `--no-wait` and poll later. |
| Low quality result | Tighten prompt details, add a negative prompt, or use `image generate` with more steps. |
| Wrong text in image | Spell exact text, specify language, and try a simpler layout. |

