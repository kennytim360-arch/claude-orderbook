"""Database storage for RORO Trading System."""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class TradingDatabase:
    """SQLite database for storing market data, signals, and trades."""

    def __init__(self, db_path: str = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            # Get project root
            project_root = Path(__file__).parent.parent.parent
            db_dir = project_root / "data" / "database"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / "trading.db"

        self.db_path = Path(db_path)
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Market data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER,
                UNIQUE(timestamp, symbol)
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp
            ON market_data(symbol, timestamp)
        """)

        # Signals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                signal_type TEXT NOT NULL,
                consensus_count INTEGER NOT NULL,
                pillar_tlt_spy TEXT,
                pillar_gld_spy TEXT,
                pillar_hyg_tlt TEXT,
                spy_rsi REAL,
                spy_price REAL,
                details TEXT
            )
        """)

        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_timestamp DATETIME NOT NULL,
                exit_timestamp DATETIME,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                exit_reason TEXT,
                pnl REAL,
                pnl_pct REAL,
                status TEXT NOT NULL
            )
        """)

        # Performance table (daily summary)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                starting_balance REAL NOT NULL,
                ending_balance REAL NOT NULL,
                daily_pnl REAL NOT NULL,
                daily_pnl_pct REAL NOT NULL,
                trades_count INTEGER NOT NULL,
                wins INTEGER NOT NULL,
                losses INTEGER NOT NULL,
                win_rate REAL
            )
        """)

        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                alert_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                message TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT 0
            )
        """)

        self.conn.commit()

    # Market Data Methods
    def insert_market_data(self, df: pd.DataFrame, symbol: str):
        """
        Insert market data into database.

        Args:
            df: DataFrame with OHLCV data (index must be datetime)
            symbol: Asset symbol
        """
        # Prepare data
        df = df.copy()
        df['symbol'] = symbol
        df['timestamp'] = df.index

        # Select columns
        columns = ['timestamp', 'symbol', 'Open', 'High', 'Low', 'Close', 'Volume']
        df_to_insert = df[columns].rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })

        # Insert (replace if exists)
        df_to_insert.to_sql(
            'market_data',
            self.conn,
            if_exists='append',
            index=False,
            method='multi'
        )
        self.conn.commit()

    def get_market_data(
        self,
        symbol: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        Retrieve market data from database.

        Args:
            symbol: Asset symbol
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            DataFrame with OHLCV data
        """
        query = "SELECT * FROM market_data WHERE symbol = ?"
        params = [symbol]

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.strftime('%Y-%m-%d %H:%M:%S'))

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.strftime('%Y-%m-%d %H:%M:%S'))

        query += " ORDER BY timestamp"

        df = pd.read_sql_query(query, self.conn, params=params)

        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

        return df

    # Signals Methods
    def insert_signal(self, signal_data: Dict[str, Any]):
        """
        Insert signal into database.

        Args:
            signal_data: Dictionary with signal information
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO signals (
                timestamp, signal_type, consensus_count,
                pillar_tlt_spy, pillar_gld_spy, pillar_hyg_tlt,
                spy_rsi, spy_price, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_data.get('timestamp', datetime.now()),
            signal_data.get('signal_type'),
            signal_data.get('consensus_count'),
            signal_data.get('pillar_tlt_spy'),
            signal_data.get('pillar_gld_spy'),
            signal_data.get('pillar_hyg_tlt'),
            signal_data.get('spy_rsi'),
            signal_data.get('spy_price'),
            signal_data.get('details', '')
        ))
        self.conn.commit()

    def get_recent_signals(self, limit: int = 100) -> pd.DataFrame:
        """
        Get recent signals.

        Args:
            limit: Maximum number of signals to retrieve

        Returns:
            DataFrame with signals
        """
        query = f"""
            SELECT * FROM signals
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        return pd.read_sql_query(query, self.conn)

    # Trades Methods
    def insert_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Insert new trade into database.

        Args:
            trade_data: Dictionary with trade information

        Returns:
            Trade ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO trades (
                entry_timestamp, symbol, direction, entry_price,
                quantity, stop_loss, take_profit, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data.get('entry_timestamp', datetime.now()),
            trade_data.get('symbol'),
            trade_data.get('direction'),
            trade_data.get('entry_price'),
            trade_data.get('quantity'),
            trade_data.get('stop_loss'),
            trade_data.get('take_profit'),
            trade_data.get('status', 'OPEN')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_trade(self, trade_id: int, update_data: Dict[str, Any]):
        """
        Update existing trade.

        Args:
            trade_id: Trade ID
            update_data: Dictionary with fields to update
        """
        # Build UPDATE query dynamically
        fields = []
        values = []

        for key, value in update_data.items():
            fields.append(f"{key} = ?")
            values.append(value)

        values.append(trade_id)

        query = f"UPDATE trades SET {', '.join(fields)} WHERE id = ?"

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        self.conn.commit()

    def get_open_trades(self) -> pd.DataFrame:
        """Get all open trades."""
        query = "SELECT * FROM trades WHERE status = 'OPEN' ORDER BY entry_timestamp"
        return pd.read_sql_query(query, self.conn)

    def get_all_trades(self) -> pd.DataFrame:
        """Get all trades."""
        query = "SELECT * FROM trades ORDER BY entry_timestamp DESC"
        return pd.read_sql_query(query, self.conn)

    # Performance Methods
    def insert_daily_performance(self, perf_data: Dict[str, Any]):
        """
        Insert daily performance summary.

        Args:
            perf_data: Dictionary with performance metrics
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO performance (
                date, starting_balance, ending_balance, daily_pnl,
                daily_pnl_pct, trades_count, wins, losses, win_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            perf_data.get('date'),
            perf_data.get('starting_balance'),
            perf_data.get('ending_balance'),
            perf_data.get('daily_pnl'),
            perf_data.get('daily_pnl_pct'),
            perf_data.get('trades_count'),
            perf_data.get('wins'),
            perf_data.get('losses'),
            perf_data.get('win_rate')
        ))
        self.conn.commit()

    def get_performance_history(self) -> pd.DataFrame:
        """Get performance history."""
        query = "SELECT * FROM performance ORDER BY date"
        return pd.read_sql_query(query, self.conn)

    # Alerts Methods
    def insert_alert(self, alert_data: Dict[str, Any]):
        """
        Insert alert into database.

        Args:
            alert_data: Dictionary with alert information
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (timestamp, alert_type, priority, message)
            VALUES (?, ?, ?, ?)
        """, (
            alert_data.get('timestamp', datetime.now()),
            alert_data.get('alert_type'),
            alert_data.get('priority'),
            alert_data.get('message')
        ))
        self.conn.commit()

    def get_unacknowledged_alerts(self) -> pd.DataFrame:
        """Get unacknowledged alerts."""
        query = """
            SELECT * FROM alerts
            WHERE acknowledged = 0
            ORDER BY timestamp DESC
        """
        return pd.read_sql_query(query, self.conn)

    # Utility Methods
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    # Test database
    print("Testing Trading Database...")

    db = TradingDatabase()

    # Test market data
    print("\n1. Testing market data storage...")
    test_data = pd.DataFrame({
        'Open': [450.0, 451.0],
        'High': [452.0, 453.0],
        'Low': [449.0, 450.5],
        'Close': [451.0, 452.0],
        'Volume': [1000000, 1100000]
    }, index=pd.date_range('2024-11-05 10:00', periods=2, freq='5min'))

    db.insert_market_data(test_data, 'SPY')
    print("✓ Market data inserted")

    # Test signal
    print("\n2. Testing signal storage...")
    db.insert_signal({
        'timestamp': datetime.now(),
        'signal_type': 'RISK-ON',
        'consensus_count': 2,
        'pillar_tlt_spy': 'RISK-ON',
        'pillar_gld_spy': 'RISK-ON',
        'pillar_hyg_tlt': 'NEUTRAL',
        'spy_rsi': 55.5,
        'spy_price': 451.0
    })
    print("✓ Signal inserted")

    # Test trade
    print("\n3. Testing trade storage...")
    trade_id = db.insert_trade({
        'entry_timestamp': datetime.now(),
        'symbol': 'SPY',
        'direction': 'LONG',
        'entry_price': 451.0,
        'quantity': 10,
        'stop_loss': 448.75,
        'take_profit': 455.50,
        'status': 'OPEN'
    })
    print(f"✓ Trade inserted with ID: {trade_id}")

    db.close()
    print("\n✓ Database test complete!")
    print(f"Database location: {db.db_path}")
