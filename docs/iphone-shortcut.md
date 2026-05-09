# iPhone Shortcut Setup

This is the quick phone capture path for the local Mac workflow.

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

## Notes

- Your iPhone and Mac need to be on the same network.
- If your Mac sleeps, the phone request will fail.
- For use outside your home network, put the webhook behind a real authenticated cloud endpoint rather than exposing your Mac directly.
