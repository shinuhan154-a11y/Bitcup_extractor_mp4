# Free Stream Manager

A free, static starter website for organizing and playing **video URLs you own or are authorized to stream**.

## Features
- Add a title, direct video URL, and optional thumbnail.
- Preview the video in an HTML5 player.
- Save a private list in the current browser using localStorage.
- Create a shareable player URL with the video details encoded in the URL fragment.
- No paid backend, database, or server-side video storage required.

## Important limitations
- This is **not a BitChute extractor** and does not bypass DRM, login walls, hotlink protection, or other access controls.
- Use direct MP4/HLS URLs only where the source host and your rights permit embedding/streaming. Some hosts require their official embed player.
- Browser library entries are stored only in the browser that added them. They do not sync across devices or visitors.
- Share links contain the video source URL in the URL fragment. Anyone with the link can see/use that source URL.
- Direct playback depends on the source host supporting browser playback, correct MIME types, and byte-range requests.
- For a public catalogue visible to all visitors, add a database/backend later (for example Firebase or Supabase) and review source licensing and bandwidth costs.

## Run locally
Open `index.html` in a modern browser. For best results, serve the folder using a local static server.

## Deploy free with GitHub Pages
1. Create a GitHub repository, e.g. `free-stream-manager`.
2. Upload `index.html` and this `README.md` to the repository root.
3. Open **Settings → Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**.
5. Select branch `main` and folder `/ (root)`, then Save.
6. Wait for GitHub Pages to publish the site. Use the URL shown in Pages settings.

Cloudflare Pages can also host the same static files on its free tier.

## Add to your own website
You can host this folder as a separate static site or copy the player concept into your own site. For a public streaming catalogue, do not rely on localStorage: it is per-browser only.
