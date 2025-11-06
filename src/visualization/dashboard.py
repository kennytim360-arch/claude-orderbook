"""Real-time RORO Trading Dashboard using Plotly Dash."""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine
from src.alerts.alert_manager import AlertManager
from src.utils.logger import logger
from src.utils.config_loader import config


class RORODashboard:
    """Real-time dashboard for RORO trading system."""

    def __init__(self, update_interval_seconds=60, enable_alerts=True):
        """
        Initialize dashboard.

        Args:
            update_interval_seconds: How often to refresh data (seconds)
            enable_alerts: Enable desktop/sound alerts
        """
        self.app = dash.Dash(__name__)
        self.update_interval = update_interval_seconds * 1000  # Convert to ms

        self.data_collector = DataCollector()
        self.signal_engine = SignalEngine()

        # Alert system
        self.enable_alerts = enable_alerts
        if enable_alerts:
            self.alert_manager = AlertManager(
                desktop_enabled=config.get('alerts.desktop_notifications', True),
                sound_enabled=config.get('alerts.sound_alerts', True),
                email_enabled=config.get('alerts.email_alerts', False)
            )
        else:
            self.alert_manager = None

        self.current_data = None
        self.current_signals = None
        self.previous_consensus = None  # Track signal changes

        self._setup_layout()
        self._setup_callbacks()

        logger.info(f"Dashboard initialized (alerts={'enabled' if enable_alerts else 'disabled'})")

    def _setup_layout(self):
        """Set up the dashboard layout."""

        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("🎯 RORO Trading System Dashboard",
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 10}),
                html.H3("Risk-On / Risk-Off Signal Monitor",
                       style={'textAlign': 'center', 'color': '#7f8c8d', 'marginTop': 0}),
            ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'marginBottom': '20px'}),

            # Auto-refresh interval
            dcc.Interval(
                id='interval-component',
                interval=self.update_interval,
                n_intervals=0
            ),

            # Current Signal Banner
            html.Div(id='signal-banner', style={'marginBottom': '20px'}),

            # Main Charts Row
            html.Div([
                # Left column - Ratio charts
                html.Div([
                    dcc.Graph(id='ratio-charts', style={'height': '600px'})
                ], style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                # Right column - Stats and info
                html.Div([
                    html.Div(id='current-stats', style={'marginBottom': '20px'}),
                    html.Div(id='signal-stats', style={'marginBottom': '20px'}),
                    html.Div(id='recent-signals')
                ], style={'width': '33%', 'display': 'inline-block', 'verticalAlign': 'top',
                         'paddingLeft': '20px'}),
            ]),

            # SPY Price Chart
            html.Div([
                dcc.Graph(id='spy-chart', style={'height': '400px'})
            ], style={'marginTop': '20px'}),

            # Footer
            html.Div([
                html.P(f"Last Updated: ", id='last-update',
                      style={'textAlign': 'center', 'color': '#95a5a6'}),
                html.P(f"Update Interval: {self.update_interval/1000:.0f} seconds | "
                      f"Timeframe: {config.get_timeframe()}",
                      style={'textAlign': 'center', 'color': '#95a5a6', 'fontSize': '12px'})
            ], style={'marginTop': '20px', 'padding': '10px', 'backgroundColor': '#ecf0f1'})

        ], style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'})

    def _setup_callbacks(self):
        """Set up dashboard callbacks for interactivity."""

        @self.app.callback(
            [Output('signal-banner', 'children'),
             Output('ratio-charts', 'figure'),
             Output('spy-chart', 'figure'),
             Output('current-stats', 'children'),
             Output('signal-stats', 'children'),
             Output('recent-signals', 'children'),
             Output('last-update', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            """Update all dashboard components."""

            try:
                # Load fresh data
                logger.info("Updating dashboard data...")
                self.current_data = self.data_collector.download_all_assets(period='5d')

                if len(self.current_data) < 4:
                    return self._error_state("Failed to load data")

                # Generate signals
                self.current_signals = self.signal_engine.generate_signals(self.current_data)

                # Get latest signal
                latest = self.signal_engine.get_latest_signal(self.current_signals)

                # Trigger alerts on signal change
                if self.enable_alerts and self.alert_manager:
                    current_consensus = latest['consensus']

                    # Check if consensus changed
                    if self.previous_consensus != current_consensus:
                        if current_consensus in ['RISK-ON', 'RISK-OFF']:
                            # Alert on new consensus signal
                            self.alert_manager.alert_consensus_signal(
                                consensus=current_consensus,
                                pillars=latest['pillars'],
                                spy_price=latest['spy_price'],
                                spy_rsi=latest['spy_rsi']
                            )
                            logger.info(f"🔔 Alert sent: {current_consensus} signal")

                    # Update previous consensus
                    self.previous_consensus = current_consensus

                # Create components
                banner = self._create_signal_banner(latest)
                ratio_fig = self._create_ratio_charts()
                spy_fig = self._create_spy_chart()
                stats = self._create_current_stats(latest)
                signal_stats = self._create_signal_stats()
                recent = self._create_recent_signals()
                timestamp = f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                return banner, ratio_fig, spy_fig, stats, signal_stats, recent, timestamp

            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                return self._error_state(str(e))

    def _create_signal_banner(self, latest_signal):
        """Create the top signal banner."""

        consensus = latest_signal['consensus']
        count = latest_signal['consensus_count']

        # Color coding
        colors = {
            'RISK-ON': {'bg': '#2ecc71', 'text': 'white'},
            'RISK-OFF': {'bg': '#e74c3c', 'text': 'white'},
            'NEUTRAL': {'bg': '#f39c12', 'text': 'white'}
        }

        color = colors.get(consensus, colors['NEUTRAL'])

        # Icon
        icons = {
            'RISK-ON': '📈',
            'RISK-OFF': '📉',
            'NEUTRAL': '➖'
        }
        icon = icons.get(consensus, '❓')

        return html.Div([
            html.H2(f"{icon} {consensus}",
                   style={'color': color['text'], 'marginBottom': '10px'}),
            html.H4(f"Consensus: {count}/3 Pillars",
                   style={'color': color['text'], 'marginTop': '0'}),
            html.P(f"Pillars: {latest_signal['pillars']}",
                  style={'color': color['text'], 'marginTop': '10px', 'fontSize': '16px'})
        ], style={
            'backgroundColor': color['bg'],
            'padding': '30px',
            'borderRadius': '10px',
            'textAlign': 'center',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
        })

    def _create_ratio_charts(self):
        """Create the three ratio charts with MAs."""

        signals = self.current_signals

        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('TLT/SPY Ratio (Bonds vs Equities)',
                          'GLD/SPY Ratio (Gold vs Equities)',
                          'HYG/TLT Ratio (Junk Bonds vs Safe Bonds)'),
            vertical_spacing=0.1
        )

        # Ratio 1: TLT/SPY
        fig.add_trace(
            go.Scatter(x=signals.index, y=signals['ratio_tlt_spy'],
                      name='TLT/SPY', line=dict(color='lightgray', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=signals.index, y=signals['tlt_spy_fast'],
                      name='Fast MA', line=dict(color='blue', width=2)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=signals.index, y=signals['tlt_spy_slow'],
                      name='Slow MA', line=dict(color='red', width=2)),
            row=1, col=1
        )

        # Ratio 2: GLD/SPY
        fig.add_trace(
            go.Scatter(x=signals.index, y=signals['ratio_gld_spy'],
                      name='GLD/SPY', line=dict(color='lightgray', width=1),
                      showlegend=False),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=signals.index, y=signals['gld_spy_fast'],
                      name='Fast MA', line=dict(color='blue', width=2),
                      showlegend=False),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=signals.index, y=signals['gld_spy_slow'],
                      name='Slow MA', line=dict(color='red', width=2),
                      showlegend=False),
            row=2, col=1
        )

        # Ratio 3: HYG/TLT
        fig.add_trace(
            go.Scatter(x=signals.index, y=signals['ratio_hyg_tlt'],
                      name='HYG/TLT', line=dict(color='lightgray', width=1),
                      showlegend=False),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=signals.index, y=signals['hyg_tlt_fast'],
                      name='Fast MA', line=dict(color='blue', width=2),
                      showlegend=False),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=signals.index, y=signals['hyg_tlt_slow'],
                      name='Slow MA', line=dict(color='red', width=2),
                      showlegend=False),
            row=3, col=1
        )

        fig.update_layout(
            height=600,
            showlegend=True,
            hovermode='x unified',
            margin=dict(l=50, r=50, t=80, b=50)
        )

        return fig

    def _create_spy_chart(self):
        """Create SPY price chart with signals."""

        signals = self.current_signals
        spy = self.current_data['SPY']

        fig = go.Figure()

        # SPY candlestick
        fig.add_trace(go.Candlestick(
            x=spy.index,
            open=spy['Open'],
            high=spy['High'],
            low=spy['Low'],
            close=spy['Close'],
            name='SPY'
        ))

        # Mark RISK-ON signals
        risk_on = signals[signals['consensus'] == 'RISK-ON']
        fig.add_trace(go.Scatter(
            x=risk_on.index,
            y=risk_on['spy_price'],
            mode='markers',
            name='RISK-ON',
            marker=dict(color='green', size=8, symbol='triangle-up')
        ))

        # Mark RISK-OFF signals
        risk_off = signals[signals['consensus'] == 'RISK-OFF']
        fig.add_trace(go.Scatter(
            x=risk_off.index,
            y=risk_off['spy_price'],
            mode='markers',
            name='RISK-OFF',
            marker=dict(color='red', size=8, symbol='triangle-down')
        ))

        fig.update_layout(
            title='SPY Price with RORO Signals',
            xaxis_title='Time',
            yaxis_title='Price ($)',
            height=400,
            hovermode='x unified'
        )

        return fig

    def _create_current_stats(self, latest_signal):
        """Create current statistics panel."""

        spy_price = latest_signal['spy_price']
        spy_rsi = latest_signal['spy_rsi']

        # Check momentum
        momentum_ok, reason = self.signal_engine.check_momentum_filter(
            latest_signal['consensus'],
            spy_rsi
        )

        momentum_color = 'green' if momentum_ok else 'orange'
        momentum_icon = '✅' if momentum_ok else '⚠️'

        return html.Div([
            html.H4("📊 Current Market Data", style={'borderBottom': '2px solid #3498db',
                                                     'paddingBottom': '10px'}),
            html.P([html.Strong("SPY Price: "), f"${spy_price:.2f}"]),
            html.P([html.Strong("SPY RSI: "), f"{spy_rsi:.1f}"]),
            html.P([
                html.Strong("Momentum Filter: "),
                html.Span(f"{momentum_icon} {reason}", style={'color': momentum_color})
            ]),
        ], style={
            'backgroundColor': '#ecf0f1',
            'padding': '15px',
            'borderRadius': '5px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        })

    def _create_signal_stats(self):
        """Create signal statistics panel."""

        signals = self.current_signals

        risk_on_count = (signals['consensus'] == 'RISK-ON').sum()
        risk_off_count = (signals['consensus'] == 'RISK-OFF').sum()
        neutral_count = (signals['consensus'] == 'NEUTRAL').sum()
        total = len(signals)

        return html.Div([
            html.H4("📈 Signal Distribution", style={'borderBottom': '2px solid #2ecc71',
                                                     'paddingBottom': '10px'}),
            html.P([html.Strong("RISK-ON: "), f"{risk_on_count} ({risk_on_count/total*100:.1f}%)"]),
            html.P([html.Strong("RISK-OFF: "), f"{risk_off_count} ({risk_off_count/total*100:.1f}%)"]),
            html.P([html.Strong("NEUTRAL: "), f"{neutral_count} ({neutral_count/total*100:.1f}%)"]),
            html.P([html.Strong("Total Bars: "), f"{total}"]),
        ], style={
            'backgroundColor': '#ecf0f1',
            'padding': '15px',
            'borderRadius': '5px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        })

    def _create_recent_signals(self):
        """Create recent signals table."""

        signals = self.current_signals.tail(10)[['consensus', 'spy_price', 'spy_rsi']].copy()

        # Format
        signals['Time'] = signals.index.strftime('%H:%M')
        signals['RSI'] = signals['spy_rsi'].apply(lambda x: f"{x:.1f}")
        signals['Price'] = signals['spy_price'].apply(lambda x: f"${x:.2f}")
        signals = signals[['Time', 'consensus', 'Price', 'RSI']]
        signals.columns = ['Time', 'Signal', 'SPY', 'RSI']

        # Create table rows
        rows = []
        for idx, row in signals.iterrows():
            color = '#d4edda' if row['Signal'] == 'RISK-ON' else '#f8d7da' if row['Signal'] == 'RISK-OFF' else '#fff3cd'
            rows.append(html.Tr([
                html.Td(row['Time']),
                html.Td(row['Signal'], style={'fontWeight': 'bold'}),
                html.Td(row['SPY']),
                html.Td(row['RSI'])
            ], style={'backgroundColor': color}))

        return html.Div([
            html.H4("🕐 Recent Signals", style={'borderBottom': '2px solid #e74c3c',
                                                'paddingBottom': '10px'}),
            html.Table([
                html.Thead(html.Tr([
                    html.Th('Time'),
                    html.Th('Signal'),
                    html.Th('SPY'),
                    html.Th('RSI')
                ])),
                html.Tbody(rows)
            ], style={'width': '100%', 'fontSize': '12px'})
        ], style={
            'backgroundColor': '#ecf0f1',
            'padding': '15px',
            'borderRadius': '5px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        })

    def _error_state(self, error_msg):
        """Return error state for all components."""
        error = html.Div([
            html.H3("⚠️ Error Loading Data", style={'color': 'red'}),
            html.P(error_msg)
        ], style={'padding': '20px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px'})

        empty_fig = go.Figure()
        empty_fig.update_layout(title="No Data Available")

        return (error, empty_fig, empty_fig, error, error, error,
                f"Error: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def run(self, debug=False, port=8050):
        """
        Run the dashboard server.

        Args:
            debug: Enable debug mode
            port: Port to run on
        """
        logger.info(f"Starting dashboard on http://localhost:{port}")
        print(f"\n🚀 RORO Dashboard starting...")
        print(f"   Open your browser to: http://localhost:{port}")
        print(f"   Press Ctrl+C to stop\n")

        self.app.run(debug=debug, port=port, host='0.0.0.0')


if __name__ == "__main__":
    dashboard = RORODashboard(update_interval_seconds=60)
    dashboard.run(debug=True, port=8050)
