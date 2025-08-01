import websocket
import json
import threading
from kafka import KafkaProducer
from datetime import datetime

# Configuration
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "trades"

# Multiple crypto pairs
CRYPTO_PAIRS = [
    "btcusdt@trade",  # Bitcoin
    "ethusdt@trade",  # Ethereum
    "adausdt@trade"   # Cardano
]

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def on_message(ws, message):
    try:
        data = json.loads(message)
        # Add timestamp for processing
        data['processed_at'] = datetime.now().isoformat()
        producer.send(KAFKA_TOPIC, data)
        print(f"Sent to Kafka: {data['s']} - ${data['p']} - Qty: {data['q']}")
    except Exception as e:
        print(f"Error processing message: {e}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    print("WebSocket connection opened")

def create_websocket_connection(symbol):
    """Create WebSocket connection for a specific crypto pair"""
    ws_url = f"wss://stream.binance.com:9443/ws/{symbol}"
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    print(f"Starting WebSocket connection for {symbol}")
    ws.run_forever()

def main():
    print("Starting multi-crypto WebSocket to Kafka pipeline...")
    print(f"Monitoring pairs: {CRYPTO_PAIRS}")
    
    # Create threads for each crypto pair
    threads = []
    for pair in CRYPTO_PAIRS:
        thread = threading.Thread(target=create_websocket_connection, args=(pair,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    print("All WebSocket connections started. Press Ctrl+C to stop.")
    
    try:
        # Keep main thread alive
        while True:
            pass
    except KeyboardInterrupt:
        print("Shutting down...")
        producer.close()

if __name__ == "__main__":
    main() 