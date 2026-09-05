# Sub-skill: Generate an illustration for a post

Adds an optional image to a draft (feed illustration, carousel slide, or
quote-card) and attaches it on publish. Uses the Pixfaro image layer through
`lib.illustrate`, which returns a hosted URL that flows straight into Publora
media. Runs on any agent (Claude Code, Codex, OpenClaw).

## When this runs

- User says "add an image", "make an illustration", "make a quote-card", or
  "add a cover" for a post.
- Offer it once after a post draft is approved, when a visual would lift reach
  (LinkedIn image posts get more dwell time than plain text).

## Backends (mirrors the publish layer)

- **pixfaro** — `PIXFARO_TOKEN` (`pf_live_...`) set: the image is generated and
  attached automatically.
- **manual** — no token: the skill drafts the image prompt and asks the user to
  generate it themselves and paste the URL. Never blocks a draft.

`lib.image_backend()` reports which is active.

## Steps

1. **Pick the kind** (maps to an aspect ratio automatically):
   - `wide` / `link` (1200:628) - link-preview / single feed image (default for a text post)
   - `portrait` / `carousel` / `quote` (4:5) - feed portrait, carousel slide, quote-card
   - `square` (1:1) - generic
   Override with an explicit `aspect_ratio="w:h"` when needed.
2. **Craft the prompt.** Describe the scene concretely: subject, composition,
   style, palette. Default to a clean, non-literal, professional editorial look
   unless the Voice & Brand Profile §6 sets a `Visual style default`. Do NOT try
   to render the post's words inside the art (see overlay below).
3. **Apply brand overlay (if profile has it).** Read `../../../references/voice-profile.md`
   §6 Brand assets. If a handle, brand color, or logo is set, pass an `overlay`
   so the text/logo is composited pixel-exact (crisp even on a cheap model):
   ```python
   from lib import illustrate
   r = illustrate(
       "Minimal flat-vector lighthouse cutting through fog, calm blue palette, editorial",
       kind="wide",
       overlay={"text": "@yourhandle", "position": "bottom-right", "color": "#0A66C2"},
   )
   ```
   For a **quote-card**, put the pulled hook line in the overlay `text` (not the
   prompt) so it renders sharp: `kind="quote"`, `overlay={"text": "<hook>", ...}`.
4. **Model choice.** Default `nano-banana-2` (balanced, ~$0.08). The overlay
   handles text, so a cheap base model is fine. Only reach for `gemini-pro-image`
   when the user wants premium art. Never silently upgrade the tier.
5. **Show + confirm.** Present the returned `url` and `cost`. On approval, attach
   it when publishing: `publish("post", draft_text, target_url, media_urls=[r["url"]])`.
6. **Manual mode.** If `r["backend"] == "manual"`, show `r["message"]` (the drafted
   prompt + aspect) and ask for a pasted URL to attach.

## Refine instead of regenerating

When the user wants a tweak ("make the sky darker", "swap the headline", "more
whitespace"), do NOT regenerate from scratch. Keep the `id` from the previous
result and edit it:

```python
from lib import illustrate, refine
first = illustrate("<scene>", kind="wide")     # -> {"id": "img_...", "url": ...}
fixed = refine(first["id"], "make the background darker and increase contrast")
```

`refine` edits by `img_...` id (not URL), inherits the source shape/tier when you
omit `aspect_ratio`/`resolution`, and is cheaper + more consistent than a fresh
generation. Chain it as many times as needed.

## Cost-guard

- Each result carries `cost` and `balance_after`; if `low_balance` is True, tell
  the user the Pixfaro balance is low before generating more.
- Default to `nano-banana-2` + 1K. The premium models (`gemini-pro-image`,
  `gpt-5-image`) bill several times more - only use them when the user asks by
  name; `illustrate`/`refine` never upgrade on their own. A result's `premium`
  flag is True when a premium-priced model was used - confirm that was intended.
- `lib.available_models()` returns live pricing/latency when you need to show it.

## Multi-image grid (LinkedIn, up to 10)

LinkedIn posts can carry up to 10 images in a grid layout (not a swipeable
carousel, which the API does not support). Generate a set and attach them all:

```python
from lib import illustrate_set, publish
shots = illustrate_set(["scene A prompt", "scene B prompt", "scene C prompt"],
                       kind="wide", overlay={"text": "@handle", "color": "#0A66C2"})
urls = [s["url"] for s in shots if s.get("url")]
publish("post", draft_text, target_url, media_urls=urls)
```

`illustrate_set` takes 2-10 prompts and returns a list of `illustrate()` results
in order. LinkedIn cannot mix images with video in one post.

## Hard rules

- One image per request (`n>1` is unsupported); for a multi-image grid, use
  `illustrate_set` (it generates one prompt at a time under the hood).
- Keep real words in the `overlay`, not baked into the prompt art.
- Respect the user's cost: default to the cheap model + 1K resolution unless asked.
- Never attach an image the user has not seen and approved.
