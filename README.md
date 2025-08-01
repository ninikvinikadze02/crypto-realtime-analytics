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
processing/
  spark_streaming.py
  simple_streaming.py
storage/
  duckdb_utils.py
requirements.txt
README.md
```

## Detailed Setup Instructions

### 1. Prerequisites Installation

#### Install Java Development Kit (JDK)
For Mac M1 Pro, download and install the **ARM64 DMG Installer** from Oracle:
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

### Option 1: Simple Processing (Recommended)
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

### Option 2: Spark Processing (Advanced)
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
```bash
python storage/duckdb_utils.py
```

## How the Architecture Works

### 🔗 Connection Flow
```
Binance API ←→ Python WebSocket Client ←→ Kafka ←→ Processing Script ←→ DuckDB
```

### 📡 Data Ingestion Details

#### Binance WebSocket Connection
- **URL**: `wss://stream.binance.com:9443/ws/btcusdt@trade`
- **Protocol**: WebSocket Secure (WSS)
- **Authentication**: None required for public trade data
- **Data Format**: JSON messages with trade details

#### WebSocket Client Process
1. **Connection**: Python `websocket-client` library connects to Binance
2. **Data Reception**: Binance pushes trade data to your connection
3. **Processing**: `on_message` callback receives each trade
4. **Forwarding**: Trade data is sent to Kafka topic

#### Sample Trade Data
```json
{
  "e": "trade",           // Event type
  "E": 1754036957014,     // Event time
  "s": "BTCUSDT",         // Symbol
  "t": 5124126132,        // Trade ID
  "p": "114410.00000000", // Price
  "q": "0.00010000",      // Quantity
  "T": 1754036957014,     // Trade time
  "m": true,              // Is buyer maker
  "M": true               // Ignore
}
```

### ⚙️ Stream Processing Details

#### Window-Based Analytics
- **Window Size**: 1-minute time windows
- **Processing**: Real-time computation as windows close
- **Metrics Computed**:
  - **Average Price**: Mean price in window
  - **Price Change %**: (Max - Min) / Min * 100
  - **Volatility**: Standard deviation of prices
  - **Trade Count**: Number of trades in window

#### Processing Logic
```python
# Group trades into 1-minute windows
window_start = trade_time.replace(second=0, microsecond=0)
window_end = window_start + timedelta(minutes=1)

# Process window when it closes
if trade_time >= window_end:
    analytics = compute_analytics(trades_in_window)
    write_to_duckdb(analytics)
```

### 💾 Storage Details

#### DuckDB Schema
```sql
CREATE TABLE analytics (
    window_start TIMESTAMP,    -- Start of 1-min window
    window_end TIMESTAMP,      -- End of 1-min window
    avg_price DOUBLE,          -- Average BTC price
    price_change_pct DOUBLE,   -- Price change percentage
    volatility DOUBLE,         -- Price volatility (std dev)
    trade_count INTEGER        -- Number of trades
)
```

#### Why DuckDB?
- **Fast**: Columnar storage optimized for analytics
- **SQL**: Standard SQL interface
- **Embedded**: No separate server required
- **Analytics-optimized**: Perfect for time-series data

### 🔄 Real-Time Data Flow Timeline

1. **Trade occurs** on Binance (e.g., BTC at $114,410)
2. **WebSocket** receives trade data (milliseconds)
3. **Kafka** stores the message in `trades` topic
4. **Processor** reads from Kafka and adds to current window
5. **Every minute**, window closes and analytics are computed
6. **DuckDB** stores the aggregated results
7. **Dashboard** can query real-time analytics

### Example Processing Timeline
```
12:30:00 - Window starts
12:30:15 - Trade 1: $114,400
12:30:30 - Trade 2: $114,410  
12:30:45 - Trade 3: $114,395
12:31:00 - Window closes, analytics computed:
          Avg: $114,401.67
          Change: 0.13%
          Volatility: 7.64
          Count: 3 trades
```

## Querying Analytics

### Recent Analytics
```sql
SELECT * FROM analytics 
ORDER BY window_start DESC 
LIMIT 10;
```

### Price Trends
```sql
SELECT 
    window_start,
    avg_price,
    price_change_pct,
    volatility
FROM analytics 
WHERE window_start >= NOW() - INTERVAL '1 hour'
ORDER BY window_start;
```

### High Volatility Periods
```sql
SELECT * FROM analytics 
WHERE volatility > 50 
ORDER BY window_start DESC;
```

## Key Benefits

### Real-time Capabilities
- **Low Latency**: Data flows in milliseconds
- **Continuous Processing**: 24/7 operation
- **Live Analytics**: Current market insights

### Scalability
- **Horizontal Scaling**: Add more Kafka brokers
- **Parallel Processing**: Multiple consumers
- **Fault Tolerance**: Data replication

### Flexibility
- **Multiple Data Sources**: Add other exchanges
- **Different Analytics**: Modify processing logic
- **Various Outputs**: Add dashboards, alerts, etc.

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
```

## Next Steps & Extensions

### Immediate Enhancements
- **Dashboard**: Web UI to visualize analytics
- **Alerts**: Notifications for price spikes
- **More Metrics**: Volume analysis, trend detection

### Advanced Features
- **Machine Learning**: Price prediction models
- **Multiple Assets**: Add ETH, ADA, etc.
- **Historical Analysis**: Long-term trend analysis

## Notes
- This project uses DuckDB for analytics storage instead of PostgreSQL.
- The simple_streaming.py is recommended over spark_streaming.py for easier setup.
- Spark is included for advanced users who need distributed processing capabilities.
- You can extend the pipeline to other crypto exchanges or add more analytics as needed. 