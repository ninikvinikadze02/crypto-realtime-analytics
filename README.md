# Real-Time Data Pipeline: Streaming Crypto Analytics

## Overview
This project implements a real-time analytics pipeline that ingests crypto trade data, processes it for trends and volatility, and outputs to a live analytics database using open-source tools.

### Architecture
- **Data Ingestion:** Python script streams trade data from Binance WebSocket API and pushes to Apache Kafka.
- **Stream Processing:** Python-based processor consumes from Kafka, computes analytics (moving averages, volatility, etc.), and writes results.
- **Storage:**
  - Raw data is stored in local Parquet files.
  - Aggregated analytics are stored in DuckDB for fast querying.

## Directory Structure
```
ingestion/
  binance_ws_to_kafka.py
  multi_crypto_ws_to_kafka.py
processing/
  spark_streaming.py
  simple_streaming.py
  multi_crypto_streaming.py
storage/
  duckdb_utils.py
  multi_crypto_utils.py
requirements.txt
README.md
```

## Detailed Setup Instructions

### 1. Prerequisites Installation

#### Install Java Development Kit (JDK)
For Mac With Apple Chip, download and install the **ARM64 DMG Installer** from Oracle:
- Go to [Oracle JDK Downloads](https://www.oracle.com/java/technologies/downloads/)
- Download **ARM64 DMG Installer** (224.57 MB)
- Double-click the `.dmg` file and follow the installation wizard
- JDK will be installed in `/Library/Java/JavaVirtualMachines/`

#### Install Python Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Apache Kafka Setup

For Kafka setup instructions, please refer to the official Apache Kafka documentation:
- **Kafka Quickstart Guide**: https://kafka.apache.org/quickstart

**Note:** After setup, Kafka should be running on:
- Broker: `localhost:9092`
- Controller: `localhost:9093`

### 3. Apache Spark Setup (Optional - for Advanced Processing)

#### Download and Extract Spark
```bash
cd ~/Downloads
wget https://archive.apache.org/dist/spark/spark-4.0.0/spark-4.0.0-bin-hadoop3.tgz
tar -xzf spark-4.0.0-bin-hadoop3.tgz
cd spark-4.0.0-bin-hadoop3
```

#### Configure Spark Environment
```bash
# Copy the default configuration
cp conf/spark-env.sh.template conf/spark-env.sh

# Edit spark-env.sh to add Java options for newer JDK versions
echo 'export SPARK_DRIVER_OPTS="--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.util.concurrent=ALL-UNNAMED --add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.cs=ALL-UNNAMED --add-opens=java.base/sun.security.action=ALL-UNNAMED --add-opens=java.base/sun.security.util=ALL-UNNAMED --add-opens=java.base/javax.security.auth=ALL-UNNAMED"' >> conf/spark-env.sh

echo 'export SPARK_EXECUTOR_OPTS="--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.util.concurrent=ALL-UNNAMED --add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.cs=ALL-UNNAMED --add-opens=java.base/sun.security.action=ALL-UNNAMED --add-opens=java.base/sun.security.util=ALL-UNNAMED --add-opens=java.base/javax.security.auth=ALL-UNNAMED"' >> conf/spark-env.sh
```

#### Add Spark to PATH
```bash
# Add to your shell profile (~/.zshrc for zsh)
echo 'export SPARK_HOME=~/Downloads/spark-4.0.0-bin-hadoop3' >> ~/.zshrc
echo 'export PATH=$PATH:$SPARK_HOME/bin' >> ~/.zshrc

# Reload shell configuration
source ~/.zshrc
```

#### Verify Spark Installation
```bash
# Check Spark version
spark-submit --version

# Start Spark shell (optional)
spark-shell
```

### 4. Verify Kafka Setup
In a new terminal:
```bash
cd ~/Downloads/kafka_2.13-4.0.0

# Check if Kafka is receiving messages (after starting ingestion)
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic trades --from-beginning --max-messages 5
```

## Running the Pipeline

### Option 1: Single Crypto Processing (BTC/USDT only)
```bash
# Start data ingestion
cd /path/to/your/project
source venv/bin/activate
python ingestion/binance_ws_to_kafka.py

# In another terminal, start processing
cd /path/to/your/project
source venv/bin/activate
python processing/simple_streaming.py
```

### Option 2: Multi-Crypto Processing (BTC/USDT, ETH/USDT, ADA/USDT)
```bash
# Start multi-crypto data ingestion
cd /path/to/your/project
source venv/bin/activate
python ingestion/multi_crypto_ws_to_kafka.py

# In another terminal, start multi-crypto processing
cd /path/to/your/project
source venv/bin/activate
python processing/multi_crypto_streaming.py
```

### Option 3: Spark Processing (Advanced)
```bash
# Start data ingestion
cd /path/to/your/project
source venv/bin/activate
python ingestion/binance_ws_to_kafka.py

# In another terminal, start Spark processing
cd /path/to/your/project
source venv/bin/activate
spark-submit processing/spark_streaming.py
```

### Query Analytics

#### Single Crypto Analytics
```bash
python storage/duckdb_utils.py
```

#### Multi-Crypto Analytics Dashboard
```bash
python storage/multi_crypto_utils.py
```

## Multi-Crypto Features

### Supported Cryptocurrencies
- **BTC/USDT** (Bitcoin)
- **ETH/USDT** (Ethereum) 
- **ADA/USDT** (Cardano)

### Enhanced Analytics
- **Per-Symbol Processing**: Separate analytics for each cryptocurrency
- **Volume Analysis**: Total trading volume per symbol
- **Cross-Symbol Comparison**: Compare performance across cryptocurrencies
- **Correlation Analysis**: Price correlation between different pairs
- **Market Summary**: Overall market statistics

### Multi-Crypto Dashboard
The enhanced dashboard provides:
- 📊 **Latest Analytics**: Real-time data for all symbols
- 📈 **Volatility Ranking**: Compare volatility across cryptocurrencies
- 💰 **Volume Analysis**: Trading volume insights
- 🌐 **Market Summary**: Overall market overview

## How the Architecture Works

### 🔗 Connection Flow
```
Binance API ←→ Python WebSocket Client ←→ Kafka ←→ Processing Script ←→ DuckDB
```

### 📡 Data Ingestion Details

#### Binance WebSocket Connection
- **URL**: `wss://stream.binance.com:9443/ws/{symbol}@trade`
- **Supported Symbols**: `btcusdt`, `ethusdt`, `adausdt`
- **Protocol**: WebSocket Secure (WSS)
- **Authentication**: None required for public trade data
- **Data Format**: JSON messages with trade details

#### Multi-Crypto WebSocket Client Process
1. **Multiple Connections**: Creates separate WebSocket connections for each symbol
2. **Threading**: Uses threads to handle multiple streams simultaneously
3. **Data Reception**: Binance pushes trade data for each symbol
4. **Symbol Identification**: Each message includes the symbol (BTCUSDT, ETHUSDT, ADAUSDT)
5. **Forwarding**: Trade data is sent to Kafka topic with symbol information

#### Sample Multi-Crypto Trade Data
```json
{
  "e": "trade",           // Event type
  "E": 1754036957014,     // Event time
  "s": "ETHUSDT",         // Symbol (BTCUSDT, ETHUSDT, ADAUSDT)
  "t": 5124126132,        // Trade ID
  "p": "3450.25000000",   // Price
  "q": "0.00150000",      // Quantity
  "T": 1754036957014,     // Trade time
  "m": true,              // Is buyer maker
  "M": true,              // Ignore
  "processed_at": "2025-08-01T12:30:00"  // Processing timestamp
}
```

### ⚙️ Multi-Crypto Stream Processing Details

#### Per-Symbol Window-Based Analytics
- **Window Size**: 1-minute time windows per symbol
- **Processing**: Real-time computation as windows close for each symbol
- **Metrics Computed**:
  - **Average Price**: Mean price in window per symbol
  - **Price Change %**: (Max - Min) / Min * 100 per symbol
  - **Volatility**: Standard deviation of prices per symbol
  - **Trade Count**: Number of trades in window per symbol
  - **Total Volume**: Sum of trading volumes per symbol

#### Multi-Crypto Processing Logic
```python
# Group trades into 1-minute windows per symbol
window_start = trade_time.replace(second=0, microsecond=0)
window_end = window_start + timedelta(minutes=1)

# Process window when it closes for each symbol
if trade_time >= window_end[symbol]:
    analytics = compute_analytics(symbol, trades_in_window)
    write_to_duckdb(analytics)
```

### 💾 Enhanced Storage Details

#### Multi-Crypto DuckDB Schema
```sql
CREATE TABLE analytics (
    symbol VARCHAR,           -- Symbol (BTCUSDT, ETHUSDT, ADAUSDT)
    window_start TIMESTAMP,   -- Start of 1-min window
    window_end TIMESTAMP,     -- End of 1-min window
    avg_price DOUBLE,         -- Average price for symbol
    price_change_pct DOUBLE,  -- Price change percentage for symbol
    volatility DOUBLE,        -- Price volatility (std dev) for symbol
    trade_count INTEGER,      -- Number of trades for symbol
    total_volume DOUBLE       -- Total trading volume for symbol
)
```

### 🔄 Multi-Crypto Real-Time Data Flow Timeline

1. **Multiple trades occur** on Binance (BTC, ETH, ADA at different prices)
2. **Multiple WebSockets** receive trade data for each symbol (milliseconds)
3. **Kafka** stores all messages in `trades` topic with symbol identification
4. **Processor** reads from Kafka and adds to current window for each symbol
5. **Every minute**, windows close and analytics are computed for each symbol
6. **DuckDB** stores the aggregated results with symbol identification
7. **Dashboard** can query real-time analytics across all symbols

### Example Multi-Crypto Processing Timeline
```
12:30:00 - Windows start for all symbols
12:30:15 - BTC Trade: $114,400
12:30:20 - ETH Trade: $3,450
12:30:25 - ADA Trade: $0.45
12:30:30 - BTC Trade: $114,410
12:30:35 - ETH Trade: $3,448
12:31:00 - Windows close, analytics computed for each:
          BTC: Avg $114,405, Change 0.09%, Vol 7.07, Vol 0.0023
          ETH: Avg $3,449, Change 0.06%, Vol 1.41, Vol 0.0030
          ADA: Avg $0.45, Change 0.00%, Vol 0.00, Vol 0.0001
```

## Querying Multi-Crypto Analytics

### Latest Analytics for All Symbols
```sql
SELECT * FROM analytics 
ORDER BY window_start DESC, symbol 
LIMIT 10;
```

### Symbol Comparison
```sql
SELECT 
    symbol,
    avg_price,
    price_change_pct,
    volatility,
    total_volume
FROM analytics 
WHERE window_start = (
    SELECT MAX(window_start) FROM analytics
)
ORDER BY avg_price DESC;
```

### Volatility Ranking
```sql
SELECT 
    symbol,
    AVG(volatility) as avg_volatility
FROM analytics 
WHERE window_start >= NOW() - INTERVAL '1 hour'
GROUP BY symbol
ORDER BY avg_volatility DESC;
```

### Volume Analysis
```sql
SELECT 
    symbol,
    AVG(total_volume) as avg_volume,
    MAX(total_volume) as max_volume
FROM analytics 
WHERE window_start >= NOW() - INTERVAL '1 hour'
GROUP BY symbol
ORDER BY avg_volume DESC;
```

### Price Correlation Analysis
```sql
WITH price_data AS (
    SELECT window_start, symbol, avg_price
    FROM analytics 
    WHERE window_start >= NOW() - INTERVAL '1 hour'
)
SELECT 
    a.symbol as symbol1,
    b.symbol as symbol2,
    CORR(a.avg_price, b.avg_price) as correlation
FROM price_data a
JOIN price_data b ON a.window_start = b.window_start AND a.symbol < b.symbol
GROUP BY a.symbol, b.symbol;
```

## Key Benefits

### Real-time Capabilities
- **Low Latency**: Data flows in milliseconds for all symbols
- **Continuous Processing**: 24/7 operation across multiple cryptocurrencies
- **Live Analytics**: Current market insights for all supported pairs

### Multi-Crypto Advantages
- **Diversified Analysis**: Compare performance across different cryptocurrencies
- **Correlation Insights**: Understand relationships between crypto pairs
- **Volume Tracking**: Monitor trading activity across the market
- **Risk Assessment**: Identify most volatile and stable cryptocurrencies

### Scalability
- **Horizontal Scaling**: Add more Kafka brokers
- **Parallel Processing**: Multiple consumers for different symbols
- **Fault Tolerance**: Data replication and recovery
- **Easy Extension**: Add more cryptocurrencies by updating the symbol list

### Flexibility
- **Multiple Data Sources**: Add other exchanges
- **Different Analytics**: Modify processing logic per symbol
- **Various Outputs**: Add dashboards, alerts, etc.
- **Symbol Management**: Easy to add/remove cryptocurrencies

## Troubleshooting

### Common Issues

#### 1. Spark Java Security Issues
**Error**: `java.lang.UnsupportedOperationException: getSubject is not supported`

**Solution**: 
- Ensure you've configured the Java options in `conf/spark-env.sh`
- Use the simple_streaming.py instead for easier setup

#### 2. Kafka Connection Issues
**Error**: `Connection refused` or `No brokers available`

**Solution**:
- Ensure Kafka server is running: `netstat -an | grep 9092`
- Check if topic exists: `bin/kafka-topics.sh --list --bootstrap-server localhost:9092`

#### 3. WebSocket Connection Issues
**Error**: Connection timeout or connection refused

**Solution**:
- Check internet connection
- Verify Binance WebSocket URL is accessible
- Ensure no firewall blocking the connection

#### 4. DuckDB Import Errors
**Error**: `ModuleNotFoundError: No module named 'duckdb'`

**Solution**:
- Ensure virtual environment is activated: `source venv/bin/activate`
- Install duckdb: `pip install duckdb`

#### 5. "command not found: spark-submit"
**Solution**:
- Add Spark to PATH as shown in setup
- Or use the simple_streaming.py instead

#### 6. Multi-Crypto Processing Issues
**Error**: Missing data for some symbols

**Solution**:
- Check if all WebSocket connections are established
- Verify symbol names in the CRYPTO_PAIRS list
- Monitor console output for connection status

### Verification Commands
```bash
# Check if Kafka is running
netstat -an | grep 9092

# Check if topic exists
cd ~/Downloads/kafka_2.13-4.0.0
bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Check DuckDB file
ls -la storage/analytics.duckdb

# Check Spark installation
spark-submit --version

# Check Java version
java -version

# Test multi-crypto dashboard
python storage/multi_crypto_utils.py
```

## Next Steps & Extensions

### Immediate Enhancements
- **Dashboard**: Web UI to visualize multi-crypto analytics
- **Alerts**: Notifications for price spikes across symbols
- **More Metrics**: Advanced correlation analysis, trend detection
- **Additional Cryptocurrencies**: Add more trading pairs

### Advanced Features
- **Machine Learning**: Price prediction models for multiple cryptocurrencies
- **Portfolio Analysis**: Track performance of crypto portfolios
- **Historical Analysis**: Long-term trend analysis across symbols
- **Exchange Integration**: Add data from other exchanges

## Notes
- This project uses DuckDB for analytics storage instead of PostgreSQL.
- The simple_streaming.py is recommended over spark_streaming.py for easier setup.
- Spark is included for advanced users who need distributed processing capabilities.
- Multi-crypto functionality provides enhanced market insights and comparison capabilities.
- You can easily extend the pipeline to other crypto exchanges or add more analytics as needed. 