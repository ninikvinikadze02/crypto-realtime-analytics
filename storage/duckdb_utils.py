import duckdb

DUCKDB_PATH = "storage/analytics.duckdb"


def query_analytics(sql="SELECT * FROM analytics ORDER BY window_start DESC LIMIT 10"):
    con = duckdb.connect(DUCKDB_PATH)
    result = con.execute(sql).fetchdf()
    con.close()
    return result


def init_duckdb():
    con = duckdb.connect(DUCKDB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS analytics (window_start TIMESTAMP, window_end TIMESTAMP, avg_price DOUBLE, price_change_pct DOUBLE, volatility DOUBLE)")
    con.close()

if __name__ == "__main__":
    init_duckdb()
    print(query_analytics()) 