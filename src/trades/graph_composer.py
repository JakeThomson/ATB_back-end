from src.data_validators import date_validator
import plotly.graph_objects as go
import plotly.io
import datetime as dt
import json


def draw_open_trade_figure(trade):
    """ Draws a custom guage chart object that easily visualises how close the stock price is in relation to it's buy
        price and the tp/sl thresholds.

    :param trade: A Trade object containing the trade data.
    :return figure: A JSON object containing the figure object to be easily read by the UI.
    """
    buy_price = trade.buy_price
    current_price = trade.current_price
    take_profit = trade.take_profit
    stop_loss = trade.stop_loss

    # Scale data to fit inside a range of -1 & 1.
    relative_tp = take_profit - buy_price
    relative_sl = stop_loss - buy_price
    relative_cp = current_price - buy_price
    if relative_cp >= 0:
        cp_percent = (relative_cp / relative_tp)
    else:
        cp_percent = -(relative_cp / relative_sl)

    # Set colour and draw figure.
    colour = "mediumseagreen" if cp_percent >= 0 else "rgb(211,63,73)"
    fig = go.Figure(go.Bar(
        x=['price'],
        y=[cp_percent],
        orientation='v',
        marker=dict(color=colour),
        hoverinfo='skip'
    ))
    fig.update_xaxes(range=[-0.5, 0.5])
    fig.update_yaxes(range=[-1, 1])
    fig.add_shape(
        # Line Vertical
        dict(
            type="line",
            y0=0,
            x0=-0.5,
            y1=0,
            x1=0.50,
            line=dict(
                color="black",
                width=1,
                dash="solid"
            )
        ))
    fig.update_layout(height=30, width=12, yaxis=dict(visible=False), xaxis=dict(visible=False), hovermode=False,
                      margin=dict(t=0, l=0, r=0, b=0), plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    # Save to JSON to allow it to be saved in the MySQL table.
    fig = fig.to_json()
    return fig, cp_percent


def draw_closed_trade_figure(trade):
    """ Draws a custom Figure object that visualises where the bot bought and sold the stocks on in relation to the
        stock's recent history..

    :param trade: A Trade object containing the trade data.
    :return figure: A JSON object containing the figure object to be send to the database and read by the UI.
    """
    # Set the line colour based on the profit/loss value.
    line_colour = "mediumseagreen" if trade.sell_price > trade.buy_price else "rgb(211,63,73)"
    # Trim the dataset so that the buy/sell points are not so squeezed together on graph.
    trim_date = date_validator.validate_date(trade.buy_date - dt.timedelta(weeks=2), 1)
    trimmed_data = trade.historical_data[trim_date:trade.sell_date]
    fig = go.Figure(go.Scatter(
        x=trimmed_data.index,
        y=trimmed_data["close"],
        line=dict(color=line_colour),
        mode="lines"
    ))
    fig.update_layout(
        height=36,
        width=75,
        yaxis=dict(visible=False),
        xaxis=dict(visible=False),
        margin=dict(t=0, l=0, r=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    # Add the crosses to the graph to show where the bot bought and sold.
    fig.add_trace(dict(
        x=[trade.buy_date, trade.sell_date],
        y=[trade.buy_price, trade.sell_price],
        mode="markers",
        marker_symbol="x-thin",
        marker_line_color="rgba(0,0,0,0.9)",
        marker_line_width=2,
        marker_size=7,
        showlegend=False,
        hoverinfo='skip'
    ))
    # Save to JSON to allow it to be saved in the MySQL table.
    fig = fig.to_json()
    return fig


def create_initial_profit_loss_figure(date, total_balance):
    """ Creates a plain figure object for the profit/loss graph, this will be the graph that gets updated as the
        backtest progresses.

    :param date: The starting date in the backtest.
    :param total_balance: The starting balance in the backtest.
    :return fig: The profit/loss figure object.
    """
    fig = go.Figure(go.Scatter(
        x=[date],
        y=[total_balance],
        mode='markers',
        line=dict(color="mediumseagreen")
    ))
    fig.update_layout(
        height=37,
        width=120,
        margin=dict(t=0, l=0, r=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        yaxis=dict(visible=False),
        xaxis=dict(visible=False))
    fig = fig.to_json()
    return fig


def update_profit_loss_graph(backtest):
    """ Updates the profit/loss graph held in the backtest properties by appending values into the data.

    :param backtest: The backtest object.
    :return fig: The profit/loss figure object.
    """
    # Set the opacity of the 'start balance' line, it stays fully visible whilst the profit loss is within a 10%
    # difference range, and slowly fades out as it gets further away until it reaches 30%.
    if backtest.start_balance * 1.3 >= backtest.total_balance >= backtest.start_balance * 1.1:
        m = -1 / (backtest.start_balance * 0.2)
        alpha = m * (backtest.total_balance - (backtest.start_balance * 1.1)) + 1
    elif backtest.total_balance > backtest.start_balance * 1.3:
        alpha = 0
    elif backtest.total_balance == backtest.start_balance:
        alpha = 0
    else:
        alpha = 255
    # Load figure from JSON string to allow it to be easily modified.
    fig = plotly.io.from_json(backtest.total_profit_loss_graph)
    # Append new date and total balance to x and y tuple objects by adding them as a single element tuple.
    fig.data[0].x += (backtest.backtest_date,)
    fig.data[0].y += (backtest.total_balance,)
    # Set the line colour based on the profit/loss value.
    fig.data[0].line.color = "mediumseagreen" if backtest.total_profit_loss >=0 else "rgb(211,63,73)"
    fig.data[0].mode = "lines"
    if len(fig.data) == 1:
        fig.add_trace(
            dict(x=[backtest.start_date, backtest.backtest_date],
                 y=[backtest.start_balance, backtest.start_balance],
                 mode="lines",
                 line=dict(color=f"rgba(0,0,0,{alpha})",
                           width=1,
                           dash="dash"),
                showlegend=False))
    else:
        fig.data[1].x = (backtest.start_date, backtest.backtest_date)
        fig.data[1].line.color = f"rgba(0,0,0,{alpha})"
    fig = fig.to_json()
    return fig