# API Keys — Secure Key Management

Manage API keys securely via macOS Keychain. Never store keys in files, env vars, or logs.

**Arguments:** `<command> [service] [key]`

## Commands

### `store <service> <key>` — Save a key

```bash
security add-generic-password -s "<service>" -a "holden" -w "<key>" -U
```

The `-U` flag updates if the entry already exists. Confirm storage by retrieving it back (don't print the full key -- just confirm non-empty).

### `get <service>` — Retrieve a key

```bash
security find-generic-password -s "<service>" -a "holden" -w
```

Return the key value. Other skills should use this pattern directly in their curl commands:
```bash
TAPI_KEY=$(security find-generic-password -s "TranscriptAPI" -a "holden" -w)
```

### `list` — Show all registered keys and their status

```bash
security dump-keychain 2>/dev/null | grep -o '"svce"<blob>="[^"]*"' | sort -u
```

Cross-reference against the Known Services Registry below. For each registered service, show whether it exists in the keychain or is missing.

### `delete <service>` — Remove a key

```bash
security delete-generic-password -s "<service>" -a "holden"
```

Confirm deletion. Warn before proceeding.

### `check <service>` — Verify a key works

1. Retrieve the key
2. Confirm it's non-empty
3. If a test command exists in the registry, run it and report success/failure

## Known Services Registry

| Service Name | Purpose | Test Command |
|---|---|---|
| `TranscriptAPI` | YouTube transcript extraction | `curl -s "https://transcriptapi.com/api/v2/youtube/transcript?video_url=dQw4w9WgXcQ&format=json" -H "Authorization: Bearer <key>" \| python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'transcript' in d or 'metadata' in d else d.get('detail','FAIL'))"` |
| `limitless-api-key` | Limitless lifelog API | — |
| `hostinger-api-token` | Hostinger DNS management | — |
| `speechmatics-api-key` | Speechmatics transcription | — |
| `Simphony STS API` | Oracle Simphony POS | — |
| `Simphony STS API HOLDEN` | Simphony (personal token) | — |
| `Simphony BI API` | Simphony Business Intelligence | — |
| `sevenrooms-client-id` | SevenRooms reservation system | — |
| `sevenrooms-client-secret` | SevenRooms auth | — |
| `sevenrooms-venue-group-id` | SevenRooms venue config | — |
| `Ableton API` | Ableton music production | — |

When new services are added via `store`, suggest adding them to this registry.

## Security Rules

- **Never** print full key values in conversation output. Mask as `sk_D2ME...bzr4` (first 6 + last 4 chars).
- **Never** write keys to markdown files, logs, or any file on disk.
- **Never** include keys in git commits.
- Always use `-w` flag for retrieval (outputs just the password, no metadata).
- The `-U` flag on store ensures idempotent writes.

## Usage by Other Skills

Any skill that needs an API key should retrieve it with:
```bash
KEY=$(security find-generic-password -s "<service>" -a "holden" -w)
```

If the key is not found, tell the user to run `/apikeys store <service> <key>`.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
