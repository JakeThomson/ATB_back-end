import plotly.graph_objects as go


def draw_at_figure(trade):
    """

    :param trade: A Trade object containing the trade data.
    :return figure: A JSON object containing a small figure of the stocks price position between the TP/SL.
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
    fig = fig.to_json()
    return fig, cp_percent
