from __future__ import annotations

from pathlib import Path

import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, dcc, html


DATA_PATH = Path(__file__).resolve().parent / "data" / "lab10" / "sales.csv"

df = pd.read_csv(DATA_PATH, parse_dates=["Дата", "Месяц"])
df["Дата"] = df["Дата"].dt.date.astype(str)
regions = sorted(df["Регион"].unique())

app = dash.Dash(__name__)
app.title = "Мониторинг продаж"

app.layout = html.Div(
    [
        html.H1("Мониторинг продаж"),
        html.Label("Выберите регион:"),
        dcc.Dropdown(
            options=[{"label": region, "value": region} for region in regions],
            value=regions[0],
            clearable=False,
            id="region-select",
        ),
        html.Label("Выберите период:"),
        dcc.DatePickerRange(
            id="date-range",
            start_date=df["Дата"].min(),
            end_date=df["Дата"].max(),
            display_format="YYYY-MM-DD",
        ),
        dcc.Graph(id="time-series"),
        dcc.Graph(id="product-bar"),
    ],
    style={"maxWidth": "1200px", "margin": "0 auto", "padding": "24px"},
)


@app.callback(
    Output("time-series", "figure"),
    Output("product-bar", "figure"),
    Input("region-select", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def update_charts(region: str, start_date: str, end_date: str):
    mask = (
        (df["Регион"] == region)
        & (df["Дата"] >= start_date)
        & (df["Дата"] <= end_date)
    )
    filtered = df.loc[mask].copy()

    ts = filtered.groupby("Дата", as_index=False)["Выручка"].sum()
    fig_time = px.line(
        ts,
        x="Дата",
        y="Выручка",
        title=f"Выручка по дням ({region})",
        markers=True,
    )
    fig_time.update_layout(hovermode="x unified")

    prod = filtered.groupby("Товар", as_index=False)["Выручка"].sum()
    fig_product = px.bar(
        prod,
        x="Товар",
        y="Выручка",
        title="Выручка по товарам",
        color="Товар",
    )
    fig_product.update_layout(showlegend=False)

    return fig_time, fig_product


if __name__ == "__main__":
    app.run(debug=True)
