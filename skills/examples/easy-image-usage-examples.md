# Easy Image Usage Examples For Novita

These examples show how to use the easy-image templates inside the Novita skill. They are interaction examples, not extra commands.

## PPT Cover

User: "帮我做一个蓝色科技风 PPT 封面，主题是 AI 赋能客服"

Agent:

1. Select `references/easy-image/templates/ppt-slides.md`.
2. Use PPT size `1280x720`.
3. Build a polished English prompt with exact Chinese title text.
4. Run:

```bash
novita image flux "Create a modern technology presentation cover for the topic \"AI 赋能客服\". Deep blue corporate background, subtle geometric network lines, clean futuristic interface elements, professional enterprise AI aesthetic, spacious title area, all visible text in Simplified Chinese characters." -W 1280 -H 720 -o ./outputs
```

## Product Photo

User: "做一张无线耳机白底产品图，电商主图"

Agent:

1. Select `references/easy-image/templates/product-photo.md`.
2. Use square size `1024x1024`.
3. Run:

```bash
novita image flux "Create a clean e-commerce product photo of wireless earbuds on a seamless pure white background. Three-quarter front angle, crisp studio lighting, subtle contact shadow, premium consumer electronics finish, sharp product edges, no text, no watermark." -W 1024 -H 1024 -o ./outputs
```

## Xiaohongshu Poster

User: "生成一张小红书风格的春季护肤活动海报"

Agent:

1. Select `references/easy-image/templates/marketing-poster.md` or `social-media-grid.md`.
2. Use portrait size `768x1024`.
3. Run:

```bash
novita image flux "Create a Xiaohongshu-style spring skincare campaign poster. Fresh pastel color palette, dewy botanical ingredients, clean beauty product arrangement, soft natural light, elegant lifestyle composition, refined social media visual style, all visible text in Simplified Chinese characters." -W 768 -H 1024 -o ./outputs
```

## UI Prototype

User: "给我出一张移动端健身 App 首页 UI 概念图"

Agent:

1. Select `references/easy-image/templates/ui-prototype.md`.
2. Use mobile portrait size `576x1024` or `768x1024`.
3. Run:

```bash
novita image flux "Design a mobile fitness app home screen UI concept. Include daily workout summary, progress ring, recommended training cards, nutrition reminder, bottom tab navigation, clean high-contrast interface, modern health app aesthetic, polished product design mockup." -W 576 -H 1024 -o ./outputs
```

## Editing Existing Image

User: "把这张产品图背景换成海边日落"

Agent:

1. Use `replace-bg` because the user provided an input image and only wants the background changed.
2. Run:

```bash
novita image replace-bg product.png "A premium beach sunset background, warm golden light, soft ocean horizon, realistic product advertising composition" -o ./outputs
```

