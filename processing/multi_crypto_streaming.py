import asyncio
import json
import time
from datetime import datetime, timedelta
from kafka import KafkaConsumer
import duckdb
import pandas as pd
from collections import defaultdict

# Configuration
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "trades"
DUCKDB_PATH = "storage/analytics.duckdb"

# Global DuckDB connection
db_connection = None

# Initialize DuckDB with WAL mode for better concurrency
def init_duckdb():
    global db_connection
    db_connection = duckdb.connect(DUCKDB_PATH)
    
    # Enable WAL mode for better concurrency (allows reads during writes)
    db_connection.execute("PRAGMA journal_mode=WAL")
    
    # Drop existing table if it exists (to handle schema changes)
    db_connection.execute("DROP TABLE IF EXISTS analytics")
    
    # Create new table with multi-crypto schema
    db_connection.execute("""
        CREATE TABLE analytics (
            symbol VARCHAR,
            window_start TIMESTAMP,
            window_end TIMESTAMP,
            avg_price DOUBLE,
            price_change_pct DOUBLE,
            volatility DOUBLE,
            trade_count INTEGER,
            total_volume DOUBLE
        )
    """)

# Store trades in memory for processing (per symbol)
trades_buffer = defaultdict(list)
last_window_end = defaultdict(lambda: None)

def process_window(symbol, trades):
    if not trades:
        return None
    
    prices = [float(trade['p']) for trade in trades]
    volumes = [float(trade['q']) for trade in trades]
    min_price = min(prices)
    max_price = max(prices)
    
    analytics = {
        'symbol': symbol,
        'avg_price': sum(prices) / len(prices),
        'price_change_pct': ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0,
        'volatility': pd.Series(prices).std() if len(prices) > 1 else 0,
        'trade_count': len(trades),
        'total_volume': sum(volumes)
    }
    
    return analytics

def write_to_duckdb(analytics):
    global db_connection
    try:
        db_connection.execute("""
            INSERT INTO analytics (symbol, window_start, window_end, avg_price, price_change_pct, volatility, trade_count, total_volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            analytics['symbol'],
            analytics['window_start'],
            analytics['window_end'],
            analytics['avg_price'],
            analytics['price_change_pct'],
            analytics['volatility'],
            analytics['trade_count'],
            analytics['total_volume']
        ])
        
        # Commit the transaction to make data visible to readers
        db_connection.commit()
        
        print(f"Written analytics: {analytics['symbol']} - {analytics['window_start']} - {analytics['window_end']}")
        print(f"  Avg Price: ${analytics['avg_price']:.2f}, Change: {analytics['price_change_pct']:.2f}%")
        print(f"  Volatility: {analytics['volatility']:.2f}, Trades: {analytics['trade_count']}, Volume: {analytics['total_volume']:.4f}")
    except Exception as e:
        print(f"Error writing to DuckDB: {e}")

def process_trade(trade_data):
    global trades_buffer, last_window_end
    
    # Parse trade data
    trade = json.loads(trade_data)
    symbol = trade['s']  # e.g., 'BTCUSDT', 'ETHUSDT', 'ADAUSDT'
    trade_time = datetime.fromtimestamp(trade['T'] / 1000)
    
    # Define 1-minute windows
    window_start = trade_time.replace(second=0, microsecond=0)
    window_end = window_start + timedelta(minutes=1)
    
    # If we've moved to a new window, process the previous window
    if last_window_end[symbol] and trade_time >= last_window_end[symbol]:
        if trades_buffer[symbol]:
            analytics = process_window(symbol, trades_buffer[symbol])
            if analytics:
                analytics['window_start'] = last_window_end[symbol] - timedelta(minutes=1)
                analytics['window_end'] = last_window_end[symbol]
                write_to_duckdb(analytics)
        trades_buffer[symbol] = []
    
    # Add trade to current window
    trades_buffer[symbol].append(trade)
    last_window_end[symbol] = window_end

def cleanup():
    global db_connection
    if db_connection:
        db_connection.close()

def main():
    global db_connection
    
    print("Initializing DuckDB for multi-crypto analytics...")
    init_duckdb()
    
    print("Starting Kafka consumer for multi-crypto trades...")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda x: x.decode('utf-8'),
        auto_offset_reset='latest',
        enable_auto_commit=True
    )
    
    print("Processing multi-crypto trades...")
    print("Monitoring: BTC/USDT, ETH/USDT, ADA/USDT")
    print("Note: Database is now in WAL mode - you can read data while streaming!")
    
    try:
        for message in consumer:
            process_trade(message.value)
    except KeyboardInterrupt:
        print("Stopping consumer...")
        consumer.close()
    finally:
        cleanup()

if __name__ == "__main__":
    main() 