import asyncio
import json
import time
from datetime import datetime, timedelta
from kafka import KafkaConsumer
import duckdb
import pandas as pd

# Configuration
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "trades"
DUCKDB_PATH = "storage/analytics.duckdb"

# Initialize DuckDB
def init_duckdb():
    con = duckdb.connect(DUCKDB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            window_start TIMESTAMP,
            window_end TIMESTAMP,
            avg_price DOUBLE,
            price_change_pct DOUBLE,
            volatility DOUBLE,
            trade_count INTEGER
        )
    """)
    con.close()

# Store trades in memory for processing
trades_buffer = []
last_window_end = None

def process_window(trades):
    if not trades:
        return None
    
    prices = [float(trade['p']) for trade in trades]
    min_price = min(prices)
    max_price = max(prices)
    
    analytics = {
        'avg_price': sum(prices) / len(prices),
        'price_change_pct': ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0,
        'volatility': pd.Series(prices).std() if len(prices) > 1 else 0,
        'trade_count': len(trades)
    }
    
    return analytics

def write_to_duckdb(window_start, window_end, analytics):
    con = duckdb.connect(DUCKDB_PATH)
    con.execute("""
        INSERT INTO analytics (window_start, window_end, avg_price, price_change_pct, volatility, trade_count)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [window_start, window_end, analytics['avg_price'], analytics['price_change_pct'], analytics['volatility'], analytics['trade_count']])
    con.close()
    print(f"Written analytics: {window_start} - {window_end}, Avg Price: ${analytics['avg_price']:.2f}, Change: {analytics['price_change_pct']:.2f}%, Volatility: {analytics['volatility']:.2f}")

def process_trade(trade_data):
    global trades_buffer, last_window_end
    
    # Parse trade data
    trade = json.loads(trade_data)
    trade_time = datetime.fromtimestamp(trade['T'] / 1000)
    
    # Define 1-minute windows
    window_start = trade_time.replace(second=0, microsecond=0)
    window_end = window_start + timedelta(minutes=1)
    
    # If we've moved to a new window, process the previous window
    if last_window_end and trade_time >= last_window_end:
        if trades_buffer:
            analytics = process_window(trades_buffer)
            if analytics:
                write_to_duckdb(last_window_end - timedelta(minutes=1), last_window_end, analytics)
        trades_buffer = []
    
    # Add trade to current window
    trades_buffer.append(trade)
    last_window_end = window_end

def main():
    print("Initializing DuckDB...")
    init_duckdb()
    
    print("Starting Kafka consumer...")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda x: x.decode('utf-8'),
        auto_offset_reset='latest',
        enable_auto_commit=True
    )
    
    print("Processing trades...")
    try:
        for message in consumer:
            process_trade(message.value)
    except KeyboardInterrupt:
        print("Stopping consumer...")
        consumer.close()

if __name__ == "__main__":
    main() 