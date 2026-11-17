# Glass landing and executive introductions

Both public homepages use the same landing experience: Next.js at port 3000 and React/Vite at port 5173. Start the appropriate app with `npm ci` and `npm run dev` in `web/` or `frontend/`. The public page does not need database, model, or speech-provider credentials. Next registration links to `/signup`; Vite links to `/register`. Vite still redirects an authenticated visitor to `/app`.

## Explore the page

- Use the sun/moon button to switch themes. The initial theme follows the device; a manual choice is remembered when browser storage is available. The page also updates the browser's theme-color and color-scheme. Authenticated workspace themes are unchanged.
- Drag the 3D floor to orbit. Select any of the five departments for its spotlight and introduction. Show full team returns to the floor.
- Meet the team starts the guided CEO → Finance → Marketing → HR → Operations introduction. Play can also start the currently selected introduction; pause, previous/next and mute remain available. The final introduction ends the tour instead of looping forever.
- English browser speech synthesis starts only after Play. Captions are visible during the tour; Read the narration is available without playback. If speech is absent or fails, captions remain and the visual sequence advances on a bounded timer. Native voice availability and quality depend on the device/OS; there are no shipped audio files or paid speech calls. The guided visual is rendered 3D, not a prerecorded/exported video.
- See how it works opens a native overview dialog. Escape and Close return to the page; opening a dialog never starts a tour or creates work.

The preview is illustrative. It does not approve, create or execute business tasks, send communications or spend money. Existing business accounts and approval flows are preserved.

## Accessibility and resource use

Agent buttons and text work when WebGL is unavailable. Reduced motion removes idle movement and profile sliding. Hidden tabs stop narration and pause the tour; offscreen canvases skip WebGL renders. Geometry, listeners, intersection observers and speech are cleaned up on unmount. Glass uses a stronger translucent fill for captions/dialog text and an opaque fallback when blur is unsupported. The mobile composition shows the 3D floor directly after the headline. Self-hosted Manrope avoids a new font-provider request.

## Source and validation

`frontend/src/landing/` owns the shared React component and authored narration. The procedural scene remains `frontend/src/studio/scene.mjs`; opt-in theme calls update renderer clear color, hemisphere/directional lighting, fog and shell materials without changing authenticated scenes. Each app has a matching landing stylesheet because its PostCSS pipeline differs. Keep `frontend/src/landing/landing.css` and `web/components/landing/landing.css` synchronized.

Run frontend lint/test/build and web test/build. `scripts/studio-browser/check-landing.py` expects a production Next server on localhost:3012 and Vite on 127.0.0.1:5173, plus Python Playwright/Chromium. It uses stubbed speech callbacks to verify all five English scripts, sequencing, pause and captions; it does **not** verify audible output on a real phone. It also covers both themes, OS preference and persistence, 320–1600px overflow, popup Escape, missing speech, missing WebGL and disabled storage. Captures are ignored under `.impeccable/review/landing/`; scroll through lower sections before full-page captures to ensure compositor layers have painted. A minimal Vite remembered-business-ID read is guarded so blocked storage does not prevent the public app from starting.

The screenshot runner disables GPU compositing while retaining real SwiftShader WebGL to avoid headless black-tile capture artifacts around fixed glass overlays. This is a capture configuration, not a production rendering flag.
