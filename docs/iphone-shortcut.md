# iPhone Shortcut Setup

This is the quick phone capture path for the local Mac workflow.

What it does:

```text
iPhone Shortcut
  -> sends a topic to your Mac
  -> Mac writes the topic into topic_queue.jsonl
  -> you run the next queued topic through the local NotebookLM workflow
```

What it does not do yet:

```text
iPhone
  -> fully cloud consumer NotebookLM
```

Consumer NotebookLM still needs a logged-in browser/Mac path unless you use NotebookLM Enterprise or replace NotebookLM with a custom cloud audio generator.

## 1. Start The Mac Inbox

On your Mac:

```bash
cd research-podcast-factory
python3 scripts/topic_webhook.py --host 0.0.0.0 --port 8765
```

Find your Mac's local IP:

```bash
ipconfig getifaddr en0
```

## 2. Create The Shortcut

In Shortcuts on iPhone:

1. Add **Ask for Input**.
2. Prompt: `Podcast topic?`
3. Add **Dictionary** with:
   - `topic`: provided input
   - `mode`: `local-notebooklm`
4. Add **Get Contents of URL**.
5. URL:

```text
http://YOUR_MAC_LAN_IP:8765/topic
```

6. Method: `POST`
7. Request Body: `JSON`
8. Use the dictionary from step 3.

## 3. Verify

On your Mac:

```bash
python3 scripts/queue_worker.py --next
```

You should see a Claude Code command like:

```text
/notebook-podcast-factory Simone Weil's Christianity for a skeptical agnostic --audience "Roman, curious skeptical listener"
```

Run that command in Claude Code to start the local Mac workflow.

## 4. What Happens Next

The local workflow should:

1. curate accessible sources,
2. create or prepare the NotebookLM notebook,
3. add the source pack,
4. generate the Audio Overview,
5. download the audio,
6. upload it through `save-to-spotify`.

`save-to-spotify` is Spotify's CLI for saving personal media to Spotify. In this project, it is the last step: it takes the NotebookLM audio file and creates a Spotify episode.

## Notes

- Your iPhone and Mac need to be on the same network.
- If your Mac sleeps, the phone request will fail.
- For use outside your home network, put the webhook behind a real authenticated cloud endpoint rather than exposing your Mac directly.
