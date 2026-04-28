# Novita Image Command Selection

Use these rules after the user's image request has been expanded with the matching easy-image template.

## Default

Prefer `novita image flux` for most text-to-image workplace assets:

```bash
novita image flux "<polished prompt>" -W 1024 -H 1024 -o ./outputs
```

Why: it is synchronous, fast, inexpensive, and easy for agents to run end to end.

## Use Stable Diffusion Async

Use `novita image generate` when the user needs more control over generation settings:

- specific model selection
- multiple images in one job
- negative prompt
- sampler, CFG, seed, or step tuning
- larger batch workflow with `task wait`

```bash
novita image generate "<polished prompt>" -W 1024 -H 1024 -n 4 --steps 28 --cfg 7.5 -o ./outputs
```

## Use Editing Commands

Use editing commands when an input image is part of the request:

| Goal | Command |
|------|---------|
| Remove background | `novita image remove-bg image.png -o clean.png` |
| Replace background | `novita image replace-bg image.png "<background prompt>" -o ./outputs` |
| Restyle from source image | `novita image img2img image.png "<style prompt>"` |
| Edit masked area | `novita image inpainting image.png mask.png "<edit prompt>"` |
| Remove text | `novita image remove-text image.png -o clean.png` |
| Extend canvas | `novita image outpainting image.png "<extension prompt>" -W 1536 -H 1024` |
| Upscale | `novita image upscale image.png --scale 2` |
| Describe an image | `novita image to-prompt image.png` |

## Size Selection

| Use case | Width | Height |
|----------|-------|--------|
| PPT / presentation cover | 1280 | 720 |
| Square poster / product image | 1024 | 1024 |
| Xiaohongshu / portrait social | 768 | 1024 |
| Douyin / vertical cover | 576 | 1024 |
| WeChat article header | 1408 | 600 |
| General landscape report graphic | 1152 | 768 |

## Prompt Rules

- Prompts should be English even when the user speaks Chinese.
- If visible text is required, include the exact text in quotes and specify the language.
- Add concrete composition, lighting, material, camera, and style details only when they improve the asset.
- For brand/product/current-appearance requests, search the web first and summarize the visual facts into the prompt.
- Keep negative prompts focused: `low quality, blurry, distorted text, watermark, extra limbs, deformed objects`.

