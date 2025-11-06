"""Configuration loader for RORO Trading System."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Loads and manages system configuration from YAML files."""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to config file. If None, uses default_config.yaml
        """
        if config_path is None:
            # Get project root (assumes this file is in src/utils/)
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "default_config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path to config value (e.g., 'data.timeframe')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config = ConfigLoader()
            >>> config.get('data.timeframe')
            '5min'
            >>> config.get('risk.risk_per_trade_pct')
            1.0
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_assets(self) -> list:
        """Get list of assets to track."""
        return self.get('data.assets', ['SPY', 'TLT', 'GLD', 'HYG'])

    def get_timeframe(self) -> str:
        """Get trading timeframe."""
        return self.get('data.timeframe', '5min')

    def get_ma_periods(self) -> tuple:
        """Get moving average periods (fast, slow)."""
        fast = self.get('signals.fast_ma_period', 5)
        slow = self.get('signals.slow_ma_period', 15)
        return (fast, slow)

    def get_risk_per_trade(self) -> float:
        """Get risk per trade percentage."""
        return self.get('risk.risk_per_trade_pct', 1.0)

    def get_stop_loss_pct(self) -> float:
        """Get stop loss percentage."""
        return self.get('risk.stop_loss_pct', 0.5)

    def get_take_profit_pct(self) -> float:
        """Get take profit percentage."""
        return self.get('risk.take_profit_pct', 1.0)

    def reload(self):
        """Reload configuration from file."""
        self.config = self._load_config()

    def __repr__(self) -> str:
        return f"ConfigLoader(config_path='{self.config_path}')"


# Global config instance (can be imported by other modules)
config = ConfigLoader()


if __name__ == "__main__":
    # Test configuration loader
    print("Testing Configuration Loader...")
    print(f"Timeframe: {config.get_timeframe()}")
    print(f"Assets: {config.get_assets()}")
    print(f"MA Periods: {config.get_ma_periods()}")
    print(f"Risk per trade: {config.get_risk_per_trade()}%")
    print(f"Stop loss: {config.get_stop_loss_pct()}%")
    print(f"Take profit: {config.get_take_profit_pct()}%")
    print("\nConfiguration loaded successfully!")
