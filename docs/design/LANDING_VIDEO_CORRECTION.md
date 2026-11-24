# Public landing correction — 24 November 2026

The owner's screenshot rejected the “One launch / Every handoff” public messaging section. It is removed, including the unused walkthrough component/data and associated styles. This does not remove recorded handoffs from the authenticated boardroom. Earlier phase-2 evidence describes historical behavior.

## Fixed behavior
The old poster was a link to `/getting-started`, not a video player. Both the poster and “Watch the project video” now open a labelled native dialog and start the actual existing MP4. “Read the guide” is a separate link. English captions, native pause/seek/fullscreen, Escape/Close pausing, retry and recording download are provided. Agent narration stops before opening the movie.

The existing 62.6-second recording is H.264, 1280×800, with captions and no audio track. It covers company setup, a plan, department work, owner review and a simulated outcome using synthetic data. It is reused rather than passed off as a new recording of live integrations. No provider actions occur.

The public background now renders actual metallic Three.js torus-knot geometry behind the existing glass. Pixel ratio is capped at 1.25; drawing is limited to about 30fps and skipped while hidden/offscreen. Motion off cancels the animation loop and retains a static frame. A failed WebGL setup leaves the CSS background intact.

## Verification
- Vite lint, 63 unit tests and production build pass; Next 27 tests and production build/type checking pass.
- Shared browser suite checks five widths in dark/light on both apps, asserts the rejected section is absent, and verifies that clicking the poster starts decoding the real 1280-wide video and advances currentTime. It verifies seeking to 30 seconds, closing pauses playback, and the second video button resumes actual playback. Existing theme/motion persistence, WebGL-draw stop, non-3D/voice/storage fallback, guide routing and public no-mutation checks remain.
- Dedicated `web/tests/landing-video-error.browser.cjs` simulates a missing MP4, verifies retry/download, then restores the real response and requires advancing playback after Retry.
- Screenshots: `/tmp/landing-video-{next,vite}`; modal captures are `{dark,light}-video.png`. Review was inline against the user's rejection screenshot and the new desktop/mobile captures; no independent design approval is claimed.
- Existing Vite large-bundle/mixed-import warnings remain. No physical Safari/iOS or latency benchmark is claimed. No AWS deployment or environment publication.

Dashboard composition remains pending the references the owner said they will share. The landing fixes are complete independently of those references. User-facing conversation uses English/Roman Urdu, not Hindi script.
