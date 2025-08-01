import websocket
import json
from kafka import KafkaProducer

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "trades"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def on_message(ws, message):
    data = json.loads(message)
    producer.send(KAFKA_TOPIC, data)
    print(f"Sent to Kafka: {data}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    print("WebSocket connection opened")

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        BINANCE_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever() 