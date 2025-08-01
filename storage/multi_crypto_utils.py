import duckdb
import pandas as pd

DUCKDB_PATH = "storage/analytics.duckdb"

def query_analytics(sql="SELECT * FROM analytics ORDER BY window_start DESC LIMIT 10"):
    """Query analytics with custom SQL"""
    con = duckdb.connect(DUCKDB_PATH)
    result = con.execute(sql).fetchdf()
    con.close()
    return result

def get_latest_analytics(symbol=None, limit=5):
    """Get latest analytics for a specific symbol or all symbols"""
    if symbol:
        sql = f"SELECT * FROM analytics WHERE symbol = '{symbol}' ORDER BY window_start DESC LIMIT {limit}"
    else:
        sql = f"SELECT * FROM analytics ORDER BY window_start DESC LIMIT {limit}"
    return query_analytics(sql)

def get_symbol_comparison():
    """Compare latest analytics across all symbols"""
    sql = """
    SELECT 
        symbol,
        avg_price,
        price_change_pct,
        volatility,
        trade_count,
        total_volume,
        window_start
    FROM analytics 
    WHERE window_start = (
        SELECT MAX(window_start) FROM analytics
    )
    ORDER BY avg_price DESC
    """
    return query_analytics(sql)

def get_volatility_ranking():
    """Get symbols ranked by volatility"""
    sql = """
    SELECT 
        symbol,
        AVG(volatility) as avg_volatility,
        COUNT(*) as data_points
    FROM analytics 
    WHERE window_start >= NOW() - INTERVAL '1 hour'
    GROUP BY symbol
    ORDER BY avg_volatility DESC
    """
    return query_analytics(sql)

def get_volume_analysis():
    """Analyze trading volume across symbols"""
    sql = """
    SELECT 
        symbol,
        AVG(total_volume) as avg_volume,
        MAX(total_volume) as max_volume,
        SUM(total_volume) as total_volume_sum
    FROM analytics 
    WHERE window_start >= NOW() - INTERVAL '1 hour'
    GROUP BY symbol
    ORDER BY avg_volume DESC
    """
    return query_analytics(sql)

def get_price_trends(symbol, hours=1):
    """Get price trends for a specific symbol"""
    sql = f"""
    SELECT 
        window_start,
        avg_price,
        price_change_pct,
        volatility
    FROM analytics 
    WHERE symbol = '{symbol}' 
    AND window_start >= NOW() - INTERVAL '{hours} hour'
    ORDER BY window_start
    """
    return query_analytics(sql)

def get_correlation_analysis():
    """Analyze price correlation between symbols"""
    sql = """
    WITH price_data AS (
        SELECT 
            window_start,
            symbol,
            avg_price
        FROM analytics 
        WHERE window_start >= NOW() - INTERVAL '1 hour'
    )
    SELECT 
        a.symbol as symbol1,
        b.symbol as symbol2,
        CORR(a.avg_price, b.avg_price) as correlation
    FROM price_data a
    JOIN price_data b ON a.window_start = b.window_start AND a.symbol < b.symbol
    GROUP BY a.symbol, b.symbol
    ORDER BY correlation DESC
    """
    return query_analytics(sql)

def get_market_summary():
    """Get overall market summary"""
    sql = """
    SELECT 
        COUNT(DISTINCT symbol) as active_symbols,
        COUNT(*) as total_analytics_windows,
        AVG(avg_price) as overall_avg_price,
        AVG(volatility) as overall_avg_volatility,
        SUM(total_volume) as total_market_volume
    FROM analytics 
    WHERE window_start >= NOW() - INTERVAL '1 hour'
    """
    return query_analytics(sql)

def init_duckdb():
    """Initialize DuckDB with multi-crypto schema"""
    con = duckdb.connect(DUCKDB_PATH)
    
    # Drop existing table if it exists (to handle schema changes)
    con.execute("DROP TABLE IF EXISTS analytics")
    
    # Create new table with multi-crypto schema
    con.execute("""
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
    con.close()

def print_market_dashboard():
    """Print a formatted market dashboard"""
    print("=" * 60)
    print("CRYPTO MARKET DASHBOARD")
    print("=" * 60)
    
    # Latest analytics for each symbol
    print("\n📊 LATEST ANALYTICS:")
    latest = get_latest_analytics(limit=3)
    for _, row in latest.iterrows():
        print(f"  {row['symbol']}: ${row['avg_price']:.2f} | "
              f"Change: {row['price_change_pct']:.2f}% | "
              f"Vol: {row['volatility']:.2f} | "
              f"Trades: {row['trade_count']}")
    
    # Volatility ranking
    print("\n📈 VOLATILITY RANKING (1 hour):")
    vol_ranking = get_volatility_ranking()
    for _, row in vol_ranking.iterrows():
        print(f"  {row['symbol']}: {row['avg_volatility']:.2f}")
    
    # Volume analysis
    print("\n💰 VOLUME ANALYSIS (1 hour):")
    volume_analysis = get_volume_analysis()
    for _, row in volume_analysis.iterrows():
        print(f"  {row['symbol']}: Avg {row['avg_volume']:.4f} | "
              f"Max {row['max_volume']:.4f}")
    
    # Market summary
    print("\n🌐 MARKET SUMMARY:")
    summary = get_market_summary()
    if not summary.empty:
        row = summary.iloc[0]
        print(f"  Active Symbols: {row['active_symbols']}")
        print(f"  Total Windows: {row['total_analytics_windows']}")
        print(f"  Overall Avg Price: ${row['overall_avg_price']:.2f}")
        print(f"  Overall Volatility: {row['overall_avg_volatility']:.2f}")
        print(f"  Total Volume: {row['total_market_volume']:.4f}")
    
    print("=" * 60)

if __name__ == "__main__":
    init_duckdb()
    print_market_dashboard() 