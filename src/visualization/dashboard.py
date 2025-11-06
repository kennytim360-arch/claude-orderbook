"""Bloomberg-Style RORO Trading Dashboard - Clear Trade Signals."""

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
    """Bloomberg-style dashboard with clear trade signals."""

    def __init__(self, update_interval_seconds=60, enable_alerts=True, account_size=10000):
        """
        Initialize Bloomberg-style dashboard.

        Args:
            update_interval_seconds: How often to refresh data (seconds)
            enable_alerts: Enable desktop/sound alerts
            account_size: Account size for position sizing ($)
        """
        self.app = dash.Dash(__name__)
        self.update_interval = update_interval_seconds * 1000  # Convert to ms
        self.account_size = account_size

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
        self.previous_consensus = None

        self._setup_layout()
        self._setup_callbacks()

        logger.info(f"Bloomberg Dashboard initialized (alerts={'enabled' if enable_alerts else 'disabled'})")

    def _setup_layout(self):
        """Set up Bloomberg-style layout."""

        # Dark Bloomberg colors
        bg_dark = '#0a0e27'
        bg_panel = '#141b3d'
        text_color = '#e8e9ed'
        accent_green = '#00ff41'
        accent_red = '#ff3366'
        accent_orange = '#ff9500'

        self.app.layout = html.Div([
            # Auto-refresh
            dcc.Interval(id='interval-component', interval=self.update_interval, n_intervals=0),

            # MAIN ACTION PANEL (HUGE AT TOP)
            html.Div(id='action-panel', style={
                'marginBottom': '20px',
                'padding': '0'
            }),

            # Market Overview Row
            html.Div([
                # Left: Charts
                html.Div([
                    dcc.Graph(id='main-chart', style={'height': '500px', 'marginBottom': '10px'}),
                    dcc.Graph(id='ratio-charts', style={'height': '400px'})
                ], style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                # Right: Stats
                html.Div([
                    html.Div(id='market-stats', style={'marginBottom': '20px'}),
                    html.Div(id='recent-signals')
                ], style={'width': '28%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'}),
            ]),

            # Footer
            html.Div([
                html.P(id='last-update', style={'textAlign': 'center', 'color': '#7f8c8d', 'margin': '10px'})
            ])

        ], style={
            'fontFamily': '"Bloomberg Terminal", monospace, "Courier New"',
            'backgroundColor': bg_dark,
            'color': text_color,
            'padding': '20px',
            'minHeight': '100vh'
        })

    def _setup_callbacks(self):
        """Set up dashboard callbacks."""

        @self.app.callback(
            [Output('action-panel', 'children'),
             Output('main-chart', 'figure'),
             Output('ratio-charts', 'figure'),
             Output('market-stats', 'children'),
             Output('recent-signals', 'children'),
             Output('last-update', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            """Update all dashboard components."""

            try:
                # Load data
                logger.info("Updating dashboard data...")
                self.current_data = self.data_collector.download_all_assets(period='5d')

                if len(self.current_data) < 4:
                    return self._error_state("Failed to load data")

                # Generate signals
                self.current_signals = self.signal_engine.generate_signals(self.current_data)
                latest = self.signal_engine.get_latest_signal(self.current_signals)

                # Trigger alerts
                if self.enable_alerts and self.alert_manager:
                    current_consensus = latest['consensus']
                    if self.previous_consensus != current_consensus:
                        if current_consensus in ['RISK-ON', 'RISK-OFF']:
                            self.alert_manager.alert_consensus_signal(
                                consensus=current_consensus,
                                pillars=latest['pillars'],
                                spy_price=latest['spy_price'],
                                spy_rsi=latest['spy_rsi']
                            )
                            logger.info(f"Alert sent: {current_consensus} signal")
                    self.previous_consensus = current_consensus

                # Create components
                action_panel = self._create_action_panel(latest)
                main_chart = self._create_main_chart()
                ratio_charts = self._create_ratio_charts()
                stats = self._create_market_stats(latest)
                recent = self._create_recent_signals()
                timestamp = f"LAST UPDATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}"

                return action_panel, main_chart, ratio_charts, stats, recent, timestamp

            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                import traceback
                traceback.print_exc()
                return self._error_state(str(e))

    def _create_action_panel(self, latest_signal):
        """Create the main action panel - tells user exactly what to do."""

        consensus = latest_signal['consensus']
        spy_price = latest_signal['spy_price']
        spy_rsi = latest_signal['spy_rsi']

        # Colors
        green = '#00ff41'
        red = '#ff3366'
        orange = '#ff9500'
        bg_dark = '#141b3d'

        # Calculate trade parameters
        stop_loss_pct = 0.5  # 0.5%
        take_profit_pct = 1.0  # 1.0%
        risk_per_trade_pct = 1.0  # 1% of account

        entry_price = spy_price
        stop_loss = entry_price * (1 - stop_loss_pct / 100)
        take_profit = entry_price * (1 + take_profit_pct / 100)

        # Position sizing
        risk_amount = self.account_size * (risk_per_trade_pct / 100)
        stop_distance = entry_price - stop_loss
        position_size = int(risk_amount / stop_distance) if stop_distance > 0 else 0
        position_value = position_size * entry_price

        # Determine action
        if consensus == 'RISK-ON' and spy_rsi > 50:
            action = 'BUY'
            action_text = 'ENTER LONG POSITION'
            bg_color = green
            text_color = '#000'
            instruction = f'BUY {position_size} SHARES OF SPY AT ${entry_price:.2f}'
        elif consensus == 'RISK-OFF':
            action = 'FLAT'
            action_text = 'STAY FLAT / EXIT LONGS'
            bg_color = red
            text_color = '#fff'
            instruction = f'DO NOT ENTER - RISK-OFF ENVIRONMENT'
        else:
            action = 'WAIT'
            action_text = 'NO CLEAR SIGNAL - WAIT'
            bg_color = orange
            text_color = '#000'
            instruction = 'NEUTRAL - WAIT FOR 2/3 CONSENSUS'

        return html.Div([
            # Giant Action Signal
            html.Div([
                html.H1(action_text, style={
                    'fontSize': '48px',
                    'fontWeight': 'bold',
                    'margin': '0',
                    'padding': '30px',
                    'textAlign': 'center',
                    'color': text_color,
                    'letterSpacing': '3px'
                })
            ], style={
                'backgroundColor': bg_color,
                'borderRadius': '10px',
                'marginBottom': '20px',
                'boxShadow': '0 8px 16px rgba(0,0,0,0.3)'
            }),

            # Trade Details (if BUY signal)
            html.Div([
                html.Div([
                    # Left Column
                    html.Div([
                        html.Div([
                            html.H3('ENTRY', style={'color': '#7f8c8d', 'margin': '0', 'fontSize': '14px'}),
                            html.H2(f'${entry_price:.2f}', style={'color': green, 'margin': '5px 0', 'fontSize': '32px'})
                        ], style={'marginBottom': '20px'}),

                        html.Div([
                            html.H3('STOP LOSS', style={'color': '#7f8c8d', 'margin': '0', 'fontSize': '14px'}),
                            html.H2(f'${stop_loss:.2f}', style={'color': red, 'margin': '5px 0', 'fontSize': '32px'}),
                            html.P(f'-{stop_loss_pct}%', style={'color': '#95a5a6', 'margin': '0'})
                        ], style={'marginBottom': '20px'}),

                        html.Div([
                            html.H3('TAKE PROFIT', style={'color': '#7f8c8d', 'margin': '0', 'fontSize': '14px'}),
                            html.H2(f'${take_profit:.2f}', style={'color': green, 'margin': '5px 0', 'fontSize': '32px'}),
                            html.P(f'+{take_profit_pct}%', style={'color': '#95a5a6', 'margin': '0'})
                        ])
                    ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px'}),

                    # Middle Column
                    html.Div([
                        html.Div([
                            html.H3('POSITION SIZE', style={'color': '#7f8c8d', 'margin': '0', 'fontSize': '14px'}),
                            html.H2(f'{position_size} shares', style={'color': '#e8e9ed', 'margin': '5px 0', 'fontSize': '32px'}),
                            html.P(f'${position_value:,.0f} value', style={'color': '#95a5a6', 'margin': '0'})
                        ], style={'marginBottom': '20px'}),

                        html.Div([
                            html.H3('RISK AMOUNT', style={'color': '#7f8c8d', 'margin': '0', 'fontSize': '14px'}),
                            html.H2(f'${risk_amount:.0f}', style={'color': orange, 'margin': '5px 0', 'fontSize': '32px'}),
                            html.P(f'{risk_per_trade_pct}% of account', style={'color': '#95a5a6', 'margin': '0'})
                        ], style={'marginBottom': '20px'}),

                        html.Div([
                            html.H3('REWARD/RISK', style={'color': '#7f8c8d', 'margin': '0', 'fontSize': '14px'}),
                            html.H2(f'2.0:1', style={'color': green, 'margin': '5px 0', 'fontSize': '32px'}),
                            html.P(f'Risk ${risk_amount:.0f} to make ${risk_amount*2:.0f}', style={'color': '#95a5a6', 'margin': '0'})
                        ])
                    ], style={'width': '35%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px', 'borderLeft': '1px solid #2c3e50', 'borderRight': '1px solid #2c3e50'}),

                    # Right Column
                    html.Div([
                        html.Div([
                            html.H3('CONSENSUS', style={'color': '#7f8c8d', 'margin': '0', 'fontSize': '14px'}),
                            html.H2(consensus, style={'color': green if consensus == 'RISK-ON' else red if consensus == 'RISK-OFF' else orange, 'margin': '5px 0', 'fontSize': '28px'}),
                            html.P(latest_signal['pillars'], style={'color': '#95a5a6', 'margin': '0', 'fontSize': '12px'})
                        ], style={'marginBottom': '20px'}),

                        html.Div([
                            html.H3('SPY RSI', style={'color': '#7f8c8d', 'margin': '0', 'fontSize': '14px'}),
                            html.H2(f'{spy_rsi:.1f}', style={'color': green if spy_rsi > 50 else red, 'margin': '5px 0', 'fontSize': '32px'}),
                            html.P('Momentum OK' if spy_rsi > 50 else 'Momentum Weak', style={'color': '#95a5a6', 'margin': '0'})
                        ], style={'marginBottom': '20px'}),

                        html.Div([
                            html.H3('WIN RATE', style={'color': '#7f8c8d', 'margin': '0', 'fontSize': '14px'}),
                            html.H2('52.9%', style={'color': green, 'margin': '5px 0', 'fontSize': '32px'}),
                            html.P('LONG-ONLY Strategy', style={'color': '#95a5a6', 'margin': '0'})
                        ])
                    ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px'})

                ], style={'display': 'flex'})
            ], style={
                'backgroundColor': bg_dark,
                'borderRadius': '10px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'
            }) if action == 'BUY' else html.Div([
                html.H3(instruction, style={
                    'textAlign': 'center',
                    'color': '#95a5a6',
                    'padding': '30px',
                    'fontSize': '24px',
                    'margin': '0'
                })
            ], style={
                'backgroundColor': bg_dark,
                'borderRadius': '10px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'
            })
        ])

    def _create_main_chart(self):
        """Create main SPY chart."""

        signals = self.current_signals
        spy = self.current_data['SPY']

        fig = go.Figure()

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=spy.index,
            open=spy['Open'],
            high=spy['High'],
            low=spy['Low'],
            close=spy['Close'],
            name='SPY',
            increasing_line_color='#00ff41',
            decreasing_line_color='#ff3366'
        ))

        # RISK-ON signals
        risk_on = signals[signals['consensus'] == 'RISK-ON']
        if len(risk_on) > 0:
            fig.add_trace(go.Scatter(
                x=risk_on.index,
                y=risk_on['spy_price'],
                mode='markers',
                name='RISK-ON (BUY)',
                marker=dict(color='#00ff41', size=12, symbol='triangle-up')
            ))

        # RISK-OFF signals
        risk_off = signals[signals['consensus'] == 'RISK-OFF']
        if len(risk_off) > 0:
            fig.add_trace(go.Scatter(
                x=risk_off.index,
                y=risk_off['spy_price'],
                mode='markers',
                name='RISK-OFF (EXIT)',
                marker=dict(color='#ff3366', size=12, symbol='triangle-down')
            ))

        fig.update_layout(
            title='SPY - S&P 500 ETF',
            plot_bgcolor='#0a0e27',
            paper_bgcolor='#141b3d',
            font=dict(color='#e8e9ed', family='monospace'),
            xaxis=dict(gridcolor='#2c3e50', showgrid=True),
            yaxis=dict(gridcolor='#2c3e50', showgrid=True),
            hovermode='x unified',
            height=500
        )

        return fig

    def _create_ratio_charts(self):
        """Create ratio charts."""

        signals = self.current_signals

        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('TLT/SPY (Bonds vs Stocks)', 'GLD/SPY (Gold vs Stocks)', 'HYG/TLT (Junk vs Safe)'),
            vertical_spacing=0.08
        )

        # TLT/SPY
        fig.add_trace(go.Scatter(x=signals.index, y=signals['ratio_tlt_spy'], name='TLT/SPY', line=dict(color='#34495e', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=signals.index, y=signals['tlt_spy_fast'], name='Fast MA', line=dict(color='#3498db', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=signals.index, y=signals['tlt_spy_slow'], name='Slow MA', line=dict(color='#e74c3c', width=2)), row=1, col=1)

        # GLD/SPY
        fig.add_trace(go.Scatter(x=signals.index, y=signals['ratio_gld_spy'], name='GLD/SPY', line=dict(color='#34495e', width=1), showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=signals.index, y=signals['gld_spy_fast'], name='Fast', line=dict(color='#3498db', width=2), showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=signals.index, y=signals['gld_spy_slow'], name='Slow', line=dict(color='#e74c3c', width=2), showlegend=False), row=2, col=1)

        # HYG/TLT
        fig.add_trace(go.Scatter(x=signals.index, y=signals['ratio_hyg_tlt'], name='HYG/TLT', line=dict(color='#34495e', width=1), showlegend=False), row=3, col=1)
        fig.add_trace(go.Scatter(x=signals.index, y=signals['hyg_tlt_fast'], name='Fast', line=dict(color='#3498db', width=2), showlegend=False), row=3, col=1)
        fig.add_trace(go.Scatter(x=signals.index, y=signals['hyg_tlt_slow'], name='Slow', line=dict(color='#e74c3c', width=2), showlegend=False), row=3, col=1)

        fig.update_layout(
            height=400,
            plot_bgcolor='#0a0e27',
            paper_bgcolor='#141b3d',
            font=dict(color='#e8e9ed', family='monospace'),
            showlegend=True,
            hovermode='x unified',
            margin=dict(l=50, r=50, t=60, b=50)
        )

        fig.update_xaxes(gridcolor='#2c3e50', showgrid=True)
        fig.update_yaxes(gridcolor='#2c3e50', showgrid=True)

        return fig

    def _create_market_stats(self, latest_signal):
        """Create market statistics panel."""

        signals = self.current_signals
        consensus = latest_signal['consensus']

        risk_on_count = (signals['consensus'] == 'RISK-ON').sum()
        risk_off_count = (signals['consensus'] == 'RISK-OFF').sum()
        neutral_count = (signals['consensus'] == 'NEUTRAL').sum()
        total = len(signals)

        return html.Div([
            html.H3('MARKET OVERVIEW', style={
                'borderBottom': '2px solid #3498db',
                'paddingBottom': '10px',
                'color': '#e8e9ed',
                'fontSize': '18px',
                'fontWeight': 'bold'
            }),

            html.Div([
                html.P('SIGNAL DISTRIBUTION', style={'color': '#7f8c8d', 'fontSize': '12px', 'margin': '15px 0 5px 0'}),
                html.P([
                    html.Span('RISK-ON: ', style={'color': '#7f8c8d'}),
                    html.Span(f'{risk_on_count} ({risk_on_count/total*100:.1f}%)', style={'color': '#00ff41', 'fontWeight': 'bold'})
                ], style={'margin': '5px 0'}),
                html.P([
                    html.Span('RISK-OFF: ', style={'color': '#7f8c8d'}),
                    html.Span(f'{risk_off_count} ({risk_off_count/total*100:.1f}%)', style={'color': '#ff3366', 'fontWeight': 'bold'})
                ], style={'margin': '5px 0'}),
                html.P([
                    html.Span('NEUTRAL: ', style={'color': '#7f8c8d'}),
                    html.Span(f'{neutral_count} ({neutral_count/total*100:.1f}%)', style={'color': '#ff9500', 'fontWeight': 'bold'})
                ], style={'margin': '5px 0'}),
            ]),

            html.Div([
                html.P('STRATEGY STATS', style={'color': '#7f8c8d', 'fontSize': '12px', 'margin': '20px 0 5px 0'}),
                html.P([
                    html.Span('Total Return: ', style={'color': '#7f8c8d'}),
                    html.Span('+32.09%', style={'color': '#00ff41', 'fontWeight': 'bold'})
                ], style={'margin': '5px 0'}),
                html.P([
                    html.Span('Win Rate: ', style={'color': '#7f8c8d'}),
                    html.Span('52.9%', style={'color': '#00ff41', 'fontWeight': 'bold'})
                ], style={'margin': '5px 0'}),
                html.P([
                    html.Span('Sharpe Ratio: ', style={'color': '#7f8c8d'}),
                    html.Span('8.77', style={'color': '#00ff41', 'fontWeight': 'bold'})
                ], style={'margin': '5px 0'}),
                html.P([
                    html.Span('Max Drawdown: ', style={'color': '#7f8c8d'}),
                    html.Span('-3.37%', style={'color': '#ff9500', 'fontWeight': 'bold'})
                ], style={'margin': '5px 0'}),
            ])

        ], style={
            'backgroundColor': '#141b3d',
            'padding': '20px',
            'borderRadius': '5px',
            'border': '1px solid #2c3e50'
        })

    def _create_recent_signals(self):
        """Create recent signals table."""

        signals_data = self.current_signals.tail(10)[['consensus', 'spy_price', 'spy_rsi']].copy()

        # Format - fix the strftime issue
        time_values = pd.to_datetime(signals_data.index).strftime('%H:%M').tolist()

        rows = []
        for idx, (index, row) in enumerate(signals_data.iterrows()):
            signal = row['consensus']
            price = row['spy_price']
            rsi = row['spy_rsi']

            color = '#00ff41' if signal == 'RISK-ON' else '#ff3366' if signal == 'RISK-OFF' else '#ff9500'

            rows.append(html.Tr([
                html.Td(time_values[idx], style={'color': '#95a5a6', 'fontSize': '11px'}),
                html.Td(signal, style={'color': color, 'fontWeight': 'bold', 'fontSize': '11px'}),
                html.Td(f'${price:.2f}', style={'color': '#e8e9ed', 'fontSize': '11px'}),
                html.Td(f'{rsi:.1f}', style={'color': '#95a5a6', 'fontSize': '11px'})
            ], style={'borderBottom': '1px solid #2c3e50'}))

        return html.Div([
            html.H3('RECENT SIGNALS', style={
                'borderBottom': '2px solid #e74c3c',
                'paddingBottom': '10px',
                'color': '#e8e9ed',
                'fontSize': '18px',
                'fontWeight': 'bold'
            }),
            html.Table([
                html.Thead(html.Tr([
                    html.Th('TIME', style={'color': '#7f8c8d', 'fontSize': '11px', 'fontWeight': 'bold'}),
                    html.Th('SIGNAL', style={'color': '#7f8c8d', 'fontSize': '11px', 'fontWeight': 'bold'}),
                    html.Th('SPY', style={'color': '#7f8c8d', 'fontSize': '11px', 'fontWeight': 'bold'}),
                    html.Th('RSI', style={'color': '#7f8c8d', 'fontSize': '11px', 'fontWeight': 'bold'})
                ])),
                html.Tbody(rows)
            ], style={'width': '100%', 'borderCollapse': 'collapse'})
        ], style={
            'backgroundColor': '#141b3d',
            'padding': '20px',
            'borderRadius': '5px',
            'border': '1px solid #2c3e50',
            'marginTop': '20px'
        })

    def _error_state(self, error_msg):
        """Return error state."""
        error = html.Div([
            html.H3("ERROR LOADING DATA", style={'color': '#ff3366'}),
            html.P(error_msg, style={'color': '#95a5a6'})
        ], style={'padding': '20px', 'backgroundColor': '#141b3d', 'borderRadius': '5px'})

        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="No Data Available",
            plot_bgcolor='#0a0e27',
            paper_bgcolor='#141b3d',
            font=dict(color='#e8e9ed')
        )

        return (error, empty_fig, empty_fig, error, error, f"ERROR: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def run(self, debug=False, port=8050):
        """Run the dashboard server."""
        logger.info(f"Starting Bloomberg Dashboard on http://localhost:{port}")
        print(f"\n" + "="*60)
        print(f"  BLOOMBERG-STYLE RORO TRADING DASHBOARD")
        print(f"="*60)
        print(f"  URL: http://localhost:{port}")
        print(f"  Mode: LONG-ONLY (52.9% win rate)")
        print(f"  Account Size: ${self.account_size:,}")
        print(f"  Press Ctrl+C to stop")
        print(f"="*60 + "\n")

        self.app.run(debug=debug, port=port, host='0.0.0.0')


if __name__ == "__main__":
    dashboard = RORODashboard(update_interval_seconds=60, account_size=10000)
    dashboard.run(debug=True, port=8050)
