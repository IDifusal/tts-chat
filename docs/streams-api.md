# Streams API

Manages the mapping between a `stream_id` (the random number in the widget URL) and a Kick channel name.

The data is stored in `data/streams.db` (SQLite), created automatically on first run.

---

## Endpoints

### List all streams

```
GET /api/streams
```

**curl example**
```bash
curl http://localhost:8000/api/streams
```

**Response**

```json
{
  "streams": [
    {
      "stream_id": "23817321123",
      "channel": "eltomallo1",
      "created_at": "2026-02-19 10:00:00",
      "running": true
    }
  ]
}
```

`running: true` means the Kick listener for that stream is currently active.

---

### Add a stream

```
POST /api/streams
Content-Type: application/json
```

**Body**

```json
{
  "stream_id": "23817321123",
  "channel": "eltomallo1"
}
```

**curl example**
```bash
curl -X POST http://bot.difusal.com/api/streams \
  -H "Content-Type: application/json" \
  -d '{"stream_id": "23817321124", "channel": "thematrixproject"}'
```

- `stream_id` — any unique string (use a random number to keep the URL hard to guess)
- `channel` — the Kick channel username

**Response** `201 Created`

```json
{
  "stream_id": "23817321123",
  "channel": "eltomallo1"
}
```

Returns `409 Conflict` if the `stream_id` already exists.

The listener starts immediately — no restart needed.

---

### Update a stream's channel

```
PUT /api/streams/{stream_id}
Content-Type: application/json
```

**Body**

```json
{
  "channel": "newchannel"
}
```

**curl example**
```bash
curl -X PUT http://localhost:8000/api/streams/23817321123 \
  -H "Content-Type: application/json" \
  -d '{"channel": "newchannel"}'
```

**Response** `200 OK`

```json
{
  "stream_id": "23817321123",
  "channel": "newchannel"
}
```

Returns `404 Not Found` if the `stream_id` does not exist.

The old listener is stopped and a new one starts for the updated channel automatically.

---

### Delete a stream

```
DELETE /api/streams/{stream_id}
```

**curl example**
```bash
curl -X DELETE http://localhost:8000/api/streams/23817321123
```

**Response** `200 OK`

```json
{
  "status": "deleted",
  "stream_id": "23817321123"
}
```

Returns `404 Not Found` if the `stream_id` does not exist.

The listener is stopped immediately.

---

## Widget URL

Once a stream is added, the OBS widget URL is:

```
http://<host>:<port>/{stream_id}
```

Example:

```
http://localhost:8000/23817321123
```

---

## curl examples

```bash
# Add
curl -X POST http://localhost:8000/api/streams \
  -H "Content-Type: application/json" \
  -d '{"stream_id": "23817321123", "channel": "eltomallo1"}'

# List
curl http://localhost:8000/api/streams

# Update channel
curl -X PUT http://localhost:8000/api/streams/23817321123 \
  -H "Content-Type: application/json" \
  -d '{"channel": "newchannel"}'

# Delete
curl -X DELETE http://localhost:8000/api/streams/23817321123
```

---

## Direct SQLite access

The database file lives at `data/streams.db`. You can inspect it with any SQLite client:

```bash
sqlite3 data/streams.db "SELECT * FROM streams;"
```

Schema:

```sql
CREATE TABLE streams (
    stream_id  TEXT PRIMARY KEY,
    channel    TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
```
