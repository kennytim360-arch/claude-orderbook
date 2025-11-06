#!/usr/bin/env python3
"""Launch the RORO Trading Dashboard."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.visualization.dashboard import RORODashboard
from src.utils.logger import logger


def main():
    """Run the dashboard."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                  RORO TRADING DASHBOARD                          ║
║                Risk-On / Risk-Off Signal Monitor                 ║
╚══════════════════════════════════════════════════════════════════╝

Starting dashboard...

📊 Features:
  - Real-time RORO consensus indicator
  - 3 ratio charts (TLT/SPY, GLD/SPY, HYG/TLT)
  - SPY price chart with signals
  - Signal statistics
  - Auto-refresh every 60 seconds

⚙️  Configuration:
  - Mode: LONG ONLY (Tested: +32% in 60 days)
  - Timeframe: 5-minute bars
  - MA Periods: 5 / 15
  - Consensus: 2 of 3 required

""")

    try:
        # Create and run dashboard
        dashboard = RORODashboard(update_interval_seconds=60)
        dashboard.run(debug=False, port=8050)

    except KeyboardInterrupt:
        print("\n\n✅ Dashboard stopped by user")
        logger.info("Dashboard stopped")

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        logger.error(f"Dashboard error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
