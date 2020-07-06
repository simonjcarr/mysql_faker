from websocket import create_connection
import json, time
ws = create_connection("ws://localhost:3333/adonis-ws")

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
