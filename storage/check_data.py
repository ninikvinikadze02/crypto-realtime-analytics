import duckdb
import pandas as pd
import os

DUCKDB_PATH = "storage/analytics.duckdb"

def check_data_wal():
    try:
        # Connect with proper WAL mode handling
        con = duckdb.connect(DUCKDB_PATH)
        
        # Check if table exists
        tables = con.execute("SHOW TABLES").fetchdf()
        print("Tables in database:")
        print(tables)
        
        if 'analytics' in tables['name'].values:
            # Get row count
            count = con.execute("SELECT COUNT(*) FROM analytics").fetchone()[0]
            print(f"\nTotal rows in analytics table: {count}")
            
            if count > 0:
                # Get latest data
                latest = con.execute("""
                    SELECT * FROM analytics 
                    ORDER BY window_start DESC 
                    LIMIT 5
                """).fetchdf()
                
                print("\nLatest 5 records:")
                print(latest)
                
                # Get summary by symbol
                summary = con.execute("""
                    SELECT 
                        symbol,
                        COUNT(*) as records,
                        MIN(window_start) as earliest,
                        MAX(window_start) as latest,
                        AVG(avg_price) as avg_price,
                        AVG(volatility) as avg_volatility
                    FROM analytics 
                    GROUP BY symbol
                    ORDER BY symbol
                """).fetchdf()
                
                print("\nSummary by symbol:")
                print(summary)
                
                # Show file sizes
                print("\nDatabase files:")
                if os.path.exists(DUCKDB_PATH):
                    print(f"  Main DB: {os.path.getsize(DUCKDB_PATH)} bytes")
                if os.path.exists(DUCKDB_PATH + ".wal"):
                    print(f"  WAL file: {os.path.getsize(DUCKDB_PATH + '.wal')} bytes")
                if os.path.exists(DUCKDB_PATH + ".shm"):
                    print(f"  SHM file: {os.path.getsize(DUCKDB_PATH + '.shm')} bytes")
            else:
                print("No data found in analytics table")
        else:
            print("Analytics table does not exist")
            
        con.close()
        
    except Exception as e:
        print(f"Error accessing database: {e}")
        print("Trying alternative connection method...")
        
        # Try alternative approach
        try:
            con = duckdb.connect(DUCKDB_PATH, read_only=True)
            count = con.execute("SELECT COUNT(*) FROM analytics").fetchone()[0]
            print(f"Successfully read {count} rows with read-only connection")
            con.close()
        except Exception as e2:
            print(f"Alternative method also failed: {e2}")

def force_checkpoint():
    """Force a checkpoint to merge WAL data into main file"""
    try:
        con = duckdb.connect(DUCKDB_PATH)
        con.execute("PRAGMA wal_checkpoint(FULL)")
        con.close()
        print("Checkpoint completed - WAL data merged to main file")
    except Exception as e:
        print(f"Checkpoint failed: {e}")

if __name__ == "__main__":
    print("Checking DuckDB data with WAL mode support...")
    check_data_wal()
    
    print("\n" + "="*50)
    print("If you still can't see data, try forcing a checkpoint:")
    force_checkpoint()
    print("Then check again:")
    check_data_wal() 