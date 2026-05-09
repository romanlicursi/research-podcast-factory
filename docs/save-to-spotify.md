# Save To Spotify

This workflow uses Spotify's [`save-to-spotify`](https://github.com/spotify/save-to-spotify) CLI.

`save-to-spotify` is for saving personal audio content to Spotify. It does not create the audio. It uploads an existing audio file and turns it into an episode in a Spotify show.

In this project:

```text
NotebookLM Audio Overview
  -> downloaded .m4a file
  -> save-to-spotify upload
  -> Spotify episode
```

Install:

```bash
curl -fsSL https://saveto.spotify.com/install.sh | bash
```

Authenticate:

```bash
save-to-spotify auth login
save-to-spotify auth status --json
```

List shows:

```bash
save-to-spotify shows --json
```

Upload an audio file:

```bash
save-to-spotify upload ./episode.m4a \
  --title "Dostoevsky and the Problem of Evil" \
  --show-id spotify:show:abc123 \
  --json
```

The workflow uses `--json` so state files can store episode IDs and avoid duplicate uploads.
