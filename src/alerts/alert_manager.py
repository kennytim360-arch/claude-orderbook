"""Alert system for RORO Trading System."""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional
from datetime import datetime
import platform

from src.utils.logger import logger


class AlertManager:
    """Manage trading alerts with multiple notification channels."""

    def __init__(
        self,
        desktop_enabled=True,
        sound_enabled=True,
        email_enabled=False
    ):
        """
        Initialize alert manager.

        Args:
            desktop_enabled: Enable desktop notifications
            sound_enabled: Enable sound alerts
            email_enabled: Enable email alerts
        """
        self.desktop_enabled = desktop_enabled
        self.sound_enabled = sound_enabled
        self.email_enabled = email_enabled

        self.last_alert_time = {}  # Cooldown tracking

        logger.info(
            f"AlertManager initialized: "
            f"Desktop={desktop_enabled}, Sound={sound_enabled}, Email={email_enabled}"
        )

    def send_alert(
        self,
        title: str,
        message: str,
        priority: str = 'INFO',
        cooldown_seconds: int = 30
    ):
        """
        Send alert through all enabled channels.

        Args:
            title: Alert title
            message: Alert message
            priority: CRITICAL, WARNING, or INFO
            cooldown_seconds: Minimum seconds between same alerts
        """
        # Check cooldown
        alert_key = f"{title}:{message}"
        now = datetime.now()

        if alert_key in self.last_alert_time:
            elapsed = (now - self.last_alert_time[alert_key]).total_seconds()
            if elapsed < cooldown_seconds:
                logger.debug(f"Alert cooldown active: {alert_key}")
                return

        self.last_alert_time[alert_key] = now

        # Send through channels
        if self.desktop_enabled:
            self._send_desktop_notification(title, message)

        if self.sound_enabled:
            self._play_alert_sound(priority)

        if self.email_enabled:
            self._send_email_alert(title, message)

        logger.info(f"Alert sent [{priority}]: {title} - {message}")

    def _send_desktop_notification(self, title: str, message: str):
        """Send desktop notification."""
        try:
            # Try using plyer (cross-platform)
            try:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    app_name='RORO Trading',
                    timeout=10
                )
                return
            except ImportError:
                pass

            # Fallback to system-specific methods
            system = platform.system()

            if system == 'Darwin':  # macOS
                import os
                os.system(f'''
                    osascript -e 'display notification "{message}" with title "{title}"'
                ''')

            elif system == 'Linux':
                import subprocess
                try:
                    subprocess.run([
                        'notify-send',
                        title,
                        message
                    ], check=True)
                except FileNotFoundError:
                    logger.warning("notify-send not available")

            elif system == 'Windows':
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=10)
                except ImportError:
                    logger.warning("win10toast not available")

        except Exception as e:
            logger.error(f"Desktop notification failed: {e}")

    def _play_alert_sound(self, priority: str):
        """Play alert sound based on priority."""
        try:
            # Try pygame first
            try:
                import pygame
                pygame.mixer.init()

                # Different sounds for different priorities
                if priority == 'CRITICAL':
                    # Play system beep multiple times
                    for _ in range(3):
                        print('\a', end='', flush=True)  # System beep
                elif priority == 'WARNING':
                    for _ in range(2):
                        print('\a', end='', flush=True)
                else:
                    print('\a', end='', flush=True)

                return
            except ImportError:
                pass

            # Fallback to system beep
            if priority == 'CRITICAL':
                for _ in range(3):
                    print('\a', end='', flush=True)
            elif priority == 'WARNING':
                for _ in range(2):
                    print('\a', end='', flush=True)
            else:
                print('\a', end='', flush=True)

        except Exception as e:
            logger.error(f"Sound alert failed: {e}")

    def _send_email_alert(self, title: str, message: str):
        """Send email alert."""
        # Placeholder for email functionality
        logger.info(f"Email alert: {title} - {message}")
        # TODO: Implement SMTP email sending

    def alert_consensus_signal(self, consensus: str, pillars: str, spy_price: float, spy_rsi: float):
        """
        Alert when consensus signal is detected.

        Args:
            consensus: RISK-ON or RISK-OFF
            pillars: Pillar names that agreed
            spy_price: Current SPY price
            spy_rsi: Current SPY RSI
        """
        if consensus == 'RISK-ON':
            title = "🟢 RISK-ON SIGNAL"
            priority = 'CRITICAL'
        elif consensus == 'RISK-OFF':
            title = "🔴 RISK-OFF SIGNAL"
            priority = 'CRITICAL'
        else:
            return  # Don't alert on NEUTRAL

        message = f"{pillars}\nSPY: ${spy_price:.2f} | RSI: {spy_rsi:.1f}"

        self.send_alert(title, message, priority=priority, cooldown_seconds=300)  # 5 min cooldown

    def alert_trade_entry(self, direction: str, price: float, stop_loss: float, take_profit: float):
        """
        Alert when trade is entered.

        Args:
            direction: LONG or SHORT
            price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        icon = "📈" if direction == "LONG" else "📉"
        title = f"{icon} {direction} Entry"
        message = (
            f"Entry: ${price:.2f}\n"
            f"Stop: ${stop_loss:.2f}\n"
            f"Target: ${take_profit:.2f}"
        )

        self.send_alert(title, message, priority='WARNING', cooldown_seconds=60)

    def alert_trade_exit(self, reason: str, pnl: float, pnl_pct: float):
        """
        Alert when trade is exited.

        Args:
            reason: Exit reason
            pnl: P&L in dollars
            pnl_pct: P&L percentage
        """
        icon = "✅" if pnl > 0 else "❌"
        title = f"{icon} Trade Closed: {reason}"
        message = f"P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)"

        priority = 'INFO' if reason == 'TAKE_PROFIT' else 'WARNING'

        self.send_alert(title, message, priority=priority, cooldown_seconds=30)

    def alert_daily_limit_reached(self, pnl: float, limit_pct: float):
        """
        Alert when daily loss limit is reached.

        Args:
            pnl: Daily P&L
            limit_pct: Loss limit percentage
        """
        title = "🛑 DAILY LOSS LIMIT REACHED"
        message = f"Daily P&L: ${pnl:.2f}\nLimit: {limit_pct}%\nSTOP TRADING!"

        self.send_alert(title, message, priority='CRITICAL', cooldown_seconds=3600)  # 1 hour

    def alert_system_error(self, error_message: str):
        """
        Alert when system error occurs.

        Args:
            error_message: Error description
        """
        title = "⚠️ SYSTEM ERROR"
        message = error_message

        self.send_alert(title, message, priority='CRITICAL', cooldown_seconds=300)


# Convenience functions
def quick_alert(message: str, priority: str = 'INFO'):
    """Quick alert without creating manager instance."""
    manager = AlertManager()
    manager.send_alert("RORO Trading", message, priority=priority)


if __name__ == "__main__":
    # Test alert system
    print("Testing Alert System...")
    print("=" * 60)

    manager = AlertManager(
        desktop_enabled=True,
        sound_enabled=True,
        email_enabled=False
    )

    # Test different alerts
    print("\n1. Testing RISK-ON alert...")
    manager.alert_consensus_signal(
        consensus='RISK-ON',
        pillars='TLT/SPY, GLD/SPY',
        spy_price=685.41,
        spy_rsi=55.2
    )

    print("\n2. Testing trade entry alert...")
    manager.alert_trade_entry(
        direction='LONG',
        price=685.41,
        stop_loss=682.00,
        take_profit=692.27
    )

    print("\n3. Testing trade exit alert...")
    manager.alert_trade_exit(
        reason='TAKE_PROFIT',
        pnl=12.50,
        pnl_pct=1.82
    )

    print("\n4. Testing error alert...")
    manager.alert_system_error("Data feed disconnected")

    print("\n" + "=" * 60)
    print("✓ Alert system test complete!")
    print("Check if you received desktop notifications and heard beeps.")
