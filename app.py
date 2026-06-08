#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 11:38:40 2026

@author: jolan
"""

import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output, State, ctx


# -----------------------------
# Basic calculation functions
# -----------------------------

def calculate_values(angle_deg, radius):
    theta = math.radians(angle_deg)

    x = radius * math.cos(theta)
    y = radius * math.sin(theta)
    d = radius - y

    return x, y, d


def make_table(selected_angles, radius):
    data = []

    for angle in sorted(selected_angles):
        x, y, d = calculate_values(angle, radius)

        data.append({
            "Angle θ (deg)": angle,
            "Lateral distance x (mm)": round(x, 2),
            "Surface height y (mm)": round(y, 2),
            "Distance to blue line d (mm)": round(d, 2),
        })

    return pd.DataFrame(data)


def make_figure(selected_angles, diameter):
    radius = diameter / 2

    # Upper semicircle
    angles_for_circle = np.linspace(0, 180, 721)
    theta = np.deg2rad(angles_for_circle)
    circle_x = radius * np.cos(theta)
    circle_y = radius * np.sin(theta)

    fig = go.Figure()

    # Circle surface with angle hover
    fig.add_trace(go.Scatter(
        x=circle_x,
        y=circle_y,
        mode="lines+markers",
        name="Circle surface",
        line=dict(width=3, color="black"),
        marker=dict(size=5, color="black", opacity=0.25),
        customdata=angles_for_circle,
        hovertemplate=(
            "Angle = %{customdata:.1f}°<br>"
           "x = %{x:.2f} mm<br>"
           "y = %{y:.2f} mm"
           "<extra></extra>"
        )
    ))

    # Invisible clickable points along the circle
    fig.add_trace(go.Scatter(
        x=circle_x,
        y=circle_y,
        mode="markers",
        name="Clickable circle points",
        marker=dict(size=10, color="rgba(0,0,0,0.01)"),
        customdata=angles_for_circle,
        hovertemplate=(
            "Click to select point<br>"
            "Angle = %{customdata:.1f}°<br>"
            "x = %{x:.2f} mm<br>"
            "y = %{y:.2f} mm"
            "<extra></extra>"
        ),
        showlegend=False
    ))

    # Blue line / top tangent
    fig.add_trace(go.Scatter(
        x=[-radius, radius],
        y=[radius, radius],
        mode="lines",
        name="Blue line / top tangent",
        line=dict(width=3)
    ))

    # Diameter
    fig.add_trace(go.Scatter(
        x=[-radius, radius],
        y=[0, 0],
        mode="lines",
        name="Diameter",
        line=dict(width=2)
    ))

    # Center point
    fig.add_trace(go.Scatter(
        x=[0],
        y=[0],
        mode="markers+text",
        name="Center",
        text=["Center"],
        textposition="bottom right",
        marker=dict(size=8)
    ))

    # Selected angle points
    for angle in sorted(selected_angles):
        x, y, d = calculate_values(angle, radius)

        # Radius line
        fig.add_trace(go.Scatter(
            x=[0, x],
            y=[0, y],
            mode="lines",
            name=f"{angle}° radius",
            showlegend=False,
            line=dict(width=2)
        ))

        # Vertical distance to blue line
        fig.add_trace(go.Scatter(
            x=[x, x],
            y=[y, radius],
            mode="lines",
            name=f"{angle}° distance to blue line",
            showlegend=False,
            line=dict(width=2, dash="dash")
        ))

        # Point and label
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode="markers+text",
            name=f"{angle}°",
            text=[f"{angle}°<br>x={x:.2f} mm<br>d={d:.2f} mm"],
            textposition="top right",
            marker=dict(size=10),
            hovertemplate=(
                f"Angle = {angle}°<br>"
                f"x = {x:.2f} mm<br>"
                f"y = {y:.2f} mm<br>"
                f"d = {d:.2f} mm<extra></extra>"
            )
        ))

    fig.update_layout(
        title=f"Interactive Circle Angle & Distance Calculator<br>Diameter = {diameter:.0f} mm, Radius = {radius:.0f} mm",
        xaxis_title="Lateral distance from center, x (mm)",
        yaxis_title="Vertical distance from center, y (mm)",
        height=700,
        clickmode="event+select",
        hovermode="closest",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5
        )
    )

    fig.update_xaxes(
        range=[-radius - 10, radius + 10],
        zeroline=True,
        scaleanchor="y",
        scaleratio=1
    )

    fig.update_yaxes(
        range=[-10, radius + 15],
        zeroline=True
    )
    
    fig.add_annotation(
        text="Developed by JET",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.45,
        showarrow=False,
        font=dict(
            size=36,
            color="rgba(100,100,100,0.18)"
        ),
        textangle=-25,
        xanchor="center",
        yanchor="middle"
    )

    return fig


def make_dash_table(df):
    if df.empty:
        return html.Div("No points selected yet.")

    return html.Table(
        [
            html.Thead(
                html.Tr([html.Th(col) for col in df.columns])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(df.iloc[i][col]) for col in df.columns
                ])
                for i in range(len(df))
            ])
        ],
        style={
            "borderCollapse": "collapse",
            "width": "100%",
            "marginTop": "20px"
        }
    )


# -----------------------------
# Dash app
# -----------------------------

app = Dash(__name__)

default_angles = [15, 30, 45, 60, 75, 90]

app.layout = html.Div(
    style={
        "fontFamily": "Arial",
        "maxWidth": "1100px",
        "margin": "auto",
        "padding": "20px"
    },
    children=[
        html.H2("Circle Angle Distance Calculator"),

        html.P(
            "Click near the upper circle surface to add an angle point. "
            "The app will automatically calculate the lateral distance x and the distance d to the blue line."
        ),

        html.Div([
            html.Label("Circle diameter (mm):"),
            dcc.Input(
                id="diameter-input",
                type="number",
                value=200,
                min=1,
                step=1,
                style={"marginLeft": "10px", "width": "120px"}
            ),
        ]),

        html.Br(),

        html.Label("Selected angles:"),
        dcc.Dropdown(
            id="angle-dropdown",
            options=[
                {"label": f"{i}°", "value": i}
                for i in range(0, 181)
            ],
            value=default_angles,
            multi=True,
            placeholder="Select or click points on the circle"
        ),

        html.Br(),

        html.Button(
            "Clear selected points",
            id="clear-button",
            n_clicks=0
        ),

        dcc.Graph(
            id="circle-graph",
            config={"displayModeBar": True}
        ),

        html.H3("Calculated Values"),
        html.Div(id="result-table")
    ]
)


# Add clicked angle to dropdown
@app.callback(
    Output("angle-dropdown", "value"),
    Input("circle-graph", "clickData"),
    Input("clear-button", "n_clicks"),
    State("angle-dropdown", "value"),
    prevent_initial_call=True
)
def update_selected_angles(click_data, clear_clicks, current_angles):
    triggered = ctx.triggered_id

    if triggered == "clear-button":
        return []

    if current_angles is None:
        current_angles = []

    if click_data is None:
        return current_angles

    point = click_data["points"][0]

    x_clicked = point["x"]
    y_clicked = point["y"]

    # Convert clicked position to angle
    angle = math.degrees(math.atan2(y_clicked, x_clicked))

    # Keep only upper semicircle angles
    angle = max(0, min(180, angle))

    # Round to nearest degree
    angle = round(angle)

    updated_angles = sorted(set(current_angles + [angle]))

    return updated_angles


# Update graph and table
@app.callback(
    Output("circle-graph", "figure"),
    Output("result-table", "children"),
    Input("angle-dropdown", "value"),
    Input("diameter-input", "value")
)
def update_output(selected_angles, diameter):
    if selected_angles is None:
        selected_angles = []

    if diameter is None or diameter <= 0:
        diameter = 200

    radius = diameter / 2

    fig = make_figure(selected_angles, diameter)
    df = make_table(selected_angles, radius)

    return fig, make_dash_table(df)


if __name__ == "__main__":
    app.run(debug=True)
