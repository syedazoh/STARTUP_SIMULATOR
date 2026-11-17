# Product walkthrough

Open `/getting-started` in either frontend. Next links to it from business selection and command center; Vite links from company setup and the workspace sidebar. Playback is optional: a native MP4 player supports pause, seek, captions and full screen, with a text checklist/transcript underneath. No account is required to read this public help page.

The recording shows the Next executive workspace with a disposable localhost identity and synthetic records. The classic Vite app uses a different setup/agent interface, explained alongside the video. Do not describe the recording as live provider execution or a production account. It is captioned and has no spoken audio track; English WebVTT captions carry the instructions.

## Reproduce the video

Install the repository's JS dependencies, Python Playwright/FastAPI/uvicorn and Chromium, plus ffmpeg. Start a **fresh** `scripts/studio-browser/fixture.py` process on 8012; never deploy it. Build/start Next on port 3012 with only the local fixture test environment documented in `scripts/studio-browser/README.md`. If Playwright asks for its ffmpeg binary, run `python -m playwright install ffmpeg` using a writable `PLAYWRIGHT_BROWSERS_PATH`. Run `python scripts/walkthrough/record.py`, then `python scripts/walkthrough/package.py`.

The recorder signs in outside the video, then records real UI interactions: business form, CEO goal/draft/activation, exact-action review, guarded synthetic approval and the refreshed result. The fixture's plan/model/results are synthetic and preseeded; this is UI guidance, not validation of plan generation, financial accuracy or external delivery. Raw video and timing files stay in `/tmp/startup-walkthrough`. No real credentials, account cookies or raw capture files are committed.

Packaged MP4, JPEG poster and VTT captions are copied to both apps' public/media folders so their separate Docker/build contexts can serve the same public tutorial. Keep these copies synchronized. MP4 uses H.264/yuv420p/faststart for native phone/browser playback and byte-range seeking. It is not loaded until the visitor requests playback. Public media has a one-hour cache; private workspace responses remain private/no-store.

## Verification

Check MP4 duration/codec/size using ffprobe; verify caption timings and matching copies. In both apps, open the help page at desktop and phone widths, play/seek/pause and load the English captions. Closing the video disclosure pauses playback. Confirm video responses support byte ranges, and Next's public-media cache exception does not change private business routes. No AWS performance claim follows from local checks.
