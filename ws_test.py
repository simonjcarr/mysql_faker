from websocket import create_connection
import json, time, os
ws = create_connection(os.getenv("WS_URL"))

ws.send(json.dumps({
  "t": 1,
  "d": {"topic": 'job'}
}))

while True:
  ws.send(json.dumps({
    "t": 7,
    "d": {
      "topic": "job",
      "event": "message",
      "data": "Hello from Python"
    }
  }))
  time.sleep(2)
