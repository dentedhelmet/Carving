# Carve a Ski Tiki

[Download the finished 84-second MP4](https://github.com/dentedhelmet/Carving/raw/refs/heads/ski-tiki-tutorial/ski-tiki-tutorial/renders/ski-tiki-tutorial.mp4)
or [download the editable project ZIP](https://github.com/dentedhelmet/Carving/raw/refs/heads/ski-tiki-tutorial/ski-tiki-tutorial/renders/ski-tiki-tutorial-editable.zip).

An 84-second portrait tutorial, built from the maker's original carving footage
and photos. Cream paper panels, timber-brown lettering and burnt-orange details
follow `DESIGN.md`. Narration uses the local Kokoro `am_michael` voice; it does
not impersonate the maker. The edit illustrates the broad process rather than
providing chainsaw or torch training. Some demonstrations are sped up.

- `index.html`: editable HyperFrames composition.
- `storyboard.json`: chapter text, narration and chosen source excerpts.
- `timeline.json`: measured scene and caption timing.
- `captions.srt`: sentence captions timed to the generated speech.
- `assets/`: selected compressed footage, photos, fonts and narration.
- Original full-resolution media remains untouched in `../assets/`.

Use the existing checkout; each cloud task is isolated, so no extra Git worktree
is needed. The CLI version is pinned by `package.json`.

```sh
cd /workspace/Carving/ski-tiki-tutorial
npm_config_cache=/tmp/npm-cache npm run check
npm_config_cache=/tmp/npm-cache npx --yes hyperframes@0.8.191 snapshot --at 4,13,23,33,43,53,63,73,81
HYPERFRAMES_BROWSER_PATH=/usr/bin/chromium npm_config_cache=/tmp/npm-cache npm run render -- --output renders/ski-tiki-tutorial.mp4 --fps 30 --quality high --workers 3
```

To regenerate narration and selected excerpts, install `kokoro-onnx`, `soundfile`,
`numpy` and `pillow` in a Python virtual environment. Download the official
Kokoro v1.0 model and voices from the `thewh1teagle/kokoro-onnx` GitHub release
`model-files-v1.0` into `/workspace/.cache/tiki-tts/`, then run:

```sh
OMP_NUM_THREADS=2 /workspace/.venvs/tiki/bin/python prepare_media.py
python3 build_composition.py
```

The browser override above uses the Chromium already installed in this cloud
environment. On another computer, omit it and let HyperFrames find its browser.

The pipeline caches generated sentence WAVs. Remove only the corresponding
`assets/voice-*.wav` files when revising narration, then regenerate.

Typefaces: Bree Serif and IBM Plex Mono (SIL Open Font License). GSAP is bundled
locally from the official 3.14.2 release. No third-party music is used.

Validation: the full runtime/layout/motion/contrast/readability check passes.
The standalone linter also emits 19 advisory messages about inline caption
wrappers; those wrappers intentionally keep sentence captions in this one
editable composition. They do not affect playback or rendering.
