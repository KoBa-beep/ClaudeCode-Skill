# Companion services (Node-RED, local bridges)

Use one when the device protocol is binary or stateful (raw TCP, persistent sessions, pairing, HID keys), when the state source is bursty, or when something must run continuously (image processing, caches). meta stays the UI layer: fast commands in, state out.

## Architecture

```
remote -> Brain -> meta --http-get--> local service (persistent device connection) --> device
                     ^                    |
                     +-- mqtt listener <--+ state: one JSON message, retained, published on change
```

- **Commands**: `http-get` to `http://127.0.0.1:<port>/cmd/<key>` (same host, host networking) or MQTT (`<device>/cmd`) when the service is a Node-RED flow. Answer **HTTP 200** with `{"status":"ok"|"error"|"unknown", ...}` so the driver can use `queryresult: "$.status"` and a fallback.
- **State**: one topic `<device>/state`, full JSON object, **retained** (meta gets it at subscription), published **only when it changes**, plus once after each reconnection to the broker. Sanitize text at the source too.
- One logical producer per topic and one consumer per command topic (duplicates double every command).
- Version marker inside the deliverable (node name, first code line, `/health` field) and a way for the user to check which version is installed.
- Secrets (API keys, tokens, pairing credentials) live in a local file or environment of the service, never in the driver or the flow file; never log them.

## Node-RED bridge (function node holding a TCP connection)

Proven design for an AV receiver (Onkyo/Integra eISCP, TCP 60128):

- one `function` node keeps **one persistent socket** in `context` (`libs: net`), a `finalize` block closes socket and timers on redeploy;
- an `inject` tick every 10 s: reconnect if needed, liveness probe every 30 s, full resync every 5 min, reconnect after 90 s without data;
- outgoing commands in a **queue with a small gap** between frames (70 ms), queue size capped;
- state kept in one object, published through a 200 ms debounce **only if the JSON differs** from the last publication;
- a **`status` node scoped to the `mqtt out` node** feeds the function: when the MQTT output turns back to connected (`msg.status.fill === "green"` after red/yellow), reset the "last published" memory and publish once. Do not rely on the status text, which may be translated;
- commands from meta arrive on `mqtt in` (`<device>/cmd`): accept a small grammar (`VOL=UP|DOWN|<n>`, `NAV=<KEY>`, `REFRESH`) plus raw commands **whitelisted by family** (regex); log and ignore anything else; enforce a volume limit in the service;
- debug output on a second node output.

eISCP essentials: 16-byte header `ISCP`, header size (UInt32BE 16), data size (UInt32BE), version byte 1, then `!1<CMD><PARAM>\r`; replies end with `\x1a\r\n`; queries are `<CMD>QSTN` (`PWR`, `AMT`, `MVL` hex volume, `SLI` input, `LMD` listening mode, `ZPW`/`ZMT`/`ZVL`/`SLZ` zone 2, `NTI`/`NAT`/`NAL` network title/artist/album...). Resync the parser on the `ISCP` marker and reject incoherent sizes. Network sources use `NTC...` navigation keys, the setup menu uses `OSD...`.

Test the real node code outside Node-RED: `new Function('msg','node','context','env','net', func)` with a fake socket (EventEmitter), fake `node.send`, fake status messages, and assertions on the number of publications.

## Python bridge (aiohttp + paho-mqtt), lessons from an Apple TV bridge

- **One persistent control connection**, reconnected in the background (every few seconds and immediately on loss). A command waits at most ~3 s for a reconnection, then answers `error` (the driver's fallback takes over).
- **Do not retry a command after a timeout** (it may have been executed: double press).
- **Serialize commands** with a lock. For HID-style keys, hold the lock from press to release and always send the release, even if the press failed (otherwise the device sees a held key). A tiny gap between press and release (~20 ms) avoids "long press" interpretation in some apps; a large one adds latency.
- **Never keep a configuration that failed**: devices may change dynamic ports (Apple TV Companion does). On connection failure, forget the cached config and rescan at once, in the same attempt.
- **One log line per command** with its outcome and duration (`command up: ok (31 ms)`, `ERROR after 3023 ms: ...`, `refused: unknown device`): it tells immediately whether a key reached the bridge.
- **Diagnostic routes**: `/health` (connections, broker, last error, version), a raw dump of what the device publishes (`/playing/raw`), the current image. They answer "what does this app really expose?" in a browser.
- **State merging** for bursty sources (see `listeners-and-state.md`) and a safety poll (every ~5 s) in case the push stream goes silent.
- Write files atomically (temp + `os.replace`), read network bodies by chunks with a limit, validate names used in paths with a whitelist.
- Clear displayed content on BACK/MENU only after the command succeeded.

## pyatv / Apple TV notes `[pyatv 0.18.0, code read + observed]`

- `pyatv.connect()` ignores its `protocol` argument and opens **every enabled service**: set `service.enabled = False` on the others to get a Companion-only connection.
- Companion covers: d-pad, `select`, `menu`, `home`, play/pause/next/previous, skip, volume, `turn_on`/`turn_off` (HID wake/sleep), app list (`{bundleId: name}`, **no icons**) and app launch. Not: `top_menu`, `stop` (map STOP to pause or use another protocol/connection).
- A separate connection (Companion + AirPlay + MRP) reads state and artwork; a fallback without Companion if the device refuses a second session.
- HID keys via `remote_control.get(Protocol.Companion).api.hid_command(down, code)`; press/release timing matters.
- **What an app exposes depends on the app**: Netflix exposes no title, no identifiers and no artwork (fields `null`, features `unavailable`); Disney+ and Plex expose artwork. Nothing can be recovered for an app that publishes nothing.
- **Artwork id can be stale** (Plex): the app announces the new title before changing the image, and pyatv caches artwork by `artwork_id`. Track the id continuously, map each id to the content shown when first seen, reject an id already mapped to another content, and publish a late image when the app announces it.
- App icons: iTunes lookup `https://itunes.apple.com/lookup?bundleId=<id>&country=<cc>` -> `artworkUrl512` (fallback `artworkUrl100`).
- Pairing (`atvremote ... pair`) reads the PIN on stdin; without a terminal, a temporary flow can feed it through a named pipe. Remove such helper routes after use.
- tvOS 26.x with pyatv 0.18.0: Companion timeouts reported on some models (pyatv issue #2845); keep the fallback path.

## Artwork search cascade (when the device gives no image)

Order that works: image from the app itself -> media server of the content (Plex `/status/sessions` + `/photo/:/transcode`, token in a header) -> local cache -> TMDB (`/search/multi`, or `/search/tv` when season/episode are parsed from the title; API key required) -> iTunes Search (no key, ~20 calls/min) -> device artwork as last resort. Parse titles (`Show - S04E03`, `3x12`, `(2010)`, drop `VF`/`VOST`/`4K` tags), normalise accents, require a similarity score (~0.72) before accepting a match, cache misses for a few hours, never pass titles through a shell. Output a square JPEG through Pillow.
