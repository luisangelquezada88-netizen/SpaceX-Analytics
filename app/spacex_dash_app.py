import os
from pathlib import Path

import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from folium.features import DivIcon

# Load the processed dataset relative to this file so the app works from any directory.
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "spacex_launch_geo.csv"
spacex_df = pd.read_csv(DATA_PATH)
max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()

# Add marker_color column for success/failure visualization
spacex_df['marker_color'] = spacex_df['class'].apply(lambda x: 'green' if x == 1 else 'red')

# Launch site coordinates for map centering
LAUNCH_SITES = {
    'CCAFS LC-40': [28.562302, -80.577356],
    'CCAFS SLC-40': [28.563197, -80.576820],
    'KSC LC-39A': [28.573255, -80.646895],
    'VAFB SLC-4E': [34.632834, -120.610745],
}

# ---- Tema visual SpaceX (sin dependencias extra, solo estilos inline) ----
THEME = {
    'bg': '#0B0D17',          # fondo página
    'card': '#151A2E',        # tarjetas
    'card_border': '#232946',
    'text': '#EAEBF0',
    'muted': '#9AA3B2',
    'accent': '#00D4FF',      # azul SpaceX
    'success': '#00E676',
    'failure': '#FF5252',
}
CARD_STYLE = {
    'backgroundColor': THEME['card'],
    'border': f"1px solid {THEME['card_border']}",
    'borderRadius': '14px',
    'padding': '18px 20px',
    'boxShadow': '0 8px 24px rgba(0,0,0,0.35)',
}
KPI_CARD = {
    **CARD_STYLE,
    'textAlign': 'center',
    'minWidth': '150px',
    'flex': '1 1 160px',  # wraps to 2 columns on phones
}

# KPIs globales (baratos de calcular una vez al importar)
TOTAL_LAUNCHES = len(spacex_df)
SUCCESS_RATE = spacex_df['class'].mean() * 100
N_SITES = spacex_df['Launch Site'].nunique()
BEST_SITE = spacex_df.groupby('Launch Site')['class'].mean().idxmax()


def style_fig(fig, title):
    """Aplica tema oscuro uniforme a las figuras Plotly."""
    fig.update_layout(
        template='plotly_dark',
        title={'text': title, 'x': 0.02, 'xanchor': 'left', 'font': {'size': 16, 'color': THEME['text']}},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': THEME['text']},
        margin={'l': 50, 'r': 30, 't': 60, 'b': 50},
        legend={'orientation': 'h', 'y': -0.2},
    )
    return fig

def create_launch_map(selected_site='All Sites'):
    """Create a Folium map with marker clusters showing launch success/failure."""
    # Default center: NASA Johnson Space Center
    nasa_coordinate = [29.559684888503615, -95.0830971930759]
    
    # Determine map center and zoom based on selection
    if selected_site != 'All Sites' and selected_site in LAUNCH_SITES:
        center = LAUNCH_SITES[selected_site]
        zoom_start = 10
    else:
        center = nasa_coordinate
        zoom_start = 4
    
    site_map = folium.Map(location=center, zoom_start=zoom_start, tiles='OpenStreetMap')
    
    # Add launch site circles with labels
    for site_name, coords in LAUNCH_SITES.items():
        circle = folium.Circle(
            coords, radius=1000, color='#d35400', fill=True, fill_opacity=0.2
        ).add_child(folium.Popup(site_name))
        marker = folium.map.Marker(
            coords,
            icon=DivIcon(
                icon_size=(20, 20),
                icon_anchor=(0, 0),
                html=f'<div style="font-size: 12; color:#d35400;"><b>{site_name}</b></div>'
            )
        )
        site_map.add_child(circle)
        site_map.add_child(marker)
    
    # Filter data based on selection
    if selected_site != 'All Sites':
        plot_df = spacex_df[spacex_df['Launch Site'] == selected_site].copy()
    else:
        plot_df = spacex_df.copy()
    
    # Create marker cluster for individual launches
    marker_cluster = MarkerCluster().add_to(site_map)
    
    for _, row in plot_df.iterrows():
        color = 'green' if row['class'] == 1 else 'red'
        icon_color = 'green' if row['class'] == 1 else 'red'
        
        folium.Marker(
            location=[row['Lat'], row['Long']],
            popup=f"{row['Launch Site']}<br>Payload: {row['Payload Mass (kg)']} kg<br>Booster: {row['Booster Version']}<br>Outcome: {'Success' if row['class'] == 1 else 'Failure'}",
            icon=folium.Icon(color='white', icon_color=icon_color, icon='info-sign', prefix='glyphicon')
        ).add_to(marker_cluster)
    
    # Add layer control
    folium.LayerControl().add_to(site_map)
    
    return site_map

# Create a dash application
# meta_tags viewport = key for mobile scaling (Dash 4 includes it by default,
# we set it explicitly so phones render at device width, like Streamlit does).
app = dash.Dash(
    __name__,
    title='SpaceX Launch Records Dashboard',
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
)
server = app.server  # Exposed for gunicorn / Render (production)

# Perf note: we do NOT pre-render the Folium map at import time.
# Rendering create_launch_map('All Sites')._repr_html_() here used to delay
# startup by 2-5s (Render healthcheck). Now the iframe starts empty and the
# update_launch_map callback fills it when the page loads.

# Create an app layout
app.layout = html.Div(
    style={'backgroundColor': THEME['bg'], 'color': THEME['text'],
           'minHeight': '100vh', 'padding': '0 0 40px 0',
           'fontFamily': 'Segoe UI, Arial, sans-serif'},
    children=[
        # Header
        html.Div(
            style={'textAlign': 'center', 'padding': '36px 20px 10px 20px'},
            children=[
                html.Div('FALCON 9  •  FIRST-STAGE RECOVERY',
                         style={'letterSpacing': '4px', 'fontSize': 12, 'color': THEME['accent']}),
                html.H1('SpaceX Launch Records Dashboard',
                        style={'margin': '8px 0 4px 0', 'fontSize': 'clamp(24px, 5vw, 38px)'}),
                html.P('Where and with which payload does Falcon 9 land best? Filter by site and payload.',
                       style={'color': THEME['muted'], 'fontSize': 15, 'margin': 0}),
            ],
        ),
        # Central container
        html.Div(
            style={'maxWidth': '1100px', 'margin': '0 auto', 'padding': '0 16px',
                   'display': 'flex', 'flexDirection': 'column', 'gap': '16px'},
            children=[
                # KPIs
                html.Div(
                    style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap'},
                    children=[
                        html.Div(style=KPI_CARD, children=[
                            html.Div('LAUNCHES', style={'fontSize': 11, 'letterSpacing': '2px', 'color': THEME['muted']}),
                            html.Div(f'{TOTAL_LAUNCHES}', style={'fontSize': 30, 'fontWeight': 'bold'}),
                        ]),
                        html.Div(style=KPI_CARD, children=[
                            html.Div('GLOBAL SUCCESS', style={'fontSize': 11, 'letterSpacing': '2px', 'color': THEME['muted']}),
                            html.Div(f'{SUCCESS_RATE:.1f}%', style={'fontSize': 30, 'fontWeight': 'bold', 'color': THEME['success']}),
                        ]),
                        html.Div(style=KPI_CARD, children=[
                            html.Div('SITES', style={'fontSize': 11, 'letterSpacing': '2px', 'color': THEME['muted']}),
                            html.Div(f'{N_SITES}', style={'fontSize': 30, 'fontWeight': 'bold'}),
                        ]),
                        html.Div(style=KPI_CARD, children=[
                            html.Div('BEST SITE', style={'fontSize': 11, 'letterSpacing': '2px', 'color': THEME['muted']}),
                            html.Div(f'{BEST_SITE}', style={'fontSize': 16, 'fontWeight': 'bold', 'color': THEME['accent']}),
                        ]),
                    ],
                ),
                # Controls
                html.Div(style=CARD_STYLE, children=[
                    html.Div('Launch Site', style={'fontSize': 12, 'letterSpacing': '2px', 'color': THEME['muted'], 'marginBottom': '6px'}),
                    dcc.Dropdown(
                        id='site-dropdown',
                        options=[
                            {'label': 'All Sites', 'value': 'All Sites'},
                            {'label': 'CCAFS LC-40', 'value': 'CCAFS LC-40'},
                            {'label': 'VAFB SLC-4E', 'value': 'VAFB SLC-4E'},
                            {'label': 'KSC LC-39A', 'value': 'KSC LC-39A'},
                            {'label': 'CCAFS SLC-40', 'value': 'CCAFS SLC-40'},
                        ],
                        placeholder='Select a Launch Site Here',
                        value='All Sites',
                        searchable=True,
                        style={'color': '#111'},
                    ),
                    html.Div('Payload range (kg)',
                             style={'fontSize': 12, 'letterSpacing': '2px', 'color': THEME['muted'],
                                    'margin': '16px 0 6px 0'}),
                    dcc.RangeSlider(
                        id='payload-slider',
                        min=0, max=10000, step=1000,
                        # 6 marks (every 2000) instead of 11: readable on phones,
                        # desktop keeps precision via drag.
                        marks={i: {'label': f'{i//1000}k', 'style': {'color': THEME['muted']}}
                               for i in range(0, 10001, 2000)},
                        value=[min_payload, max_payload],
                    ),
                ]),
                # Map
                html.Div(style=CARD_STYLE, children=[
                    html.H3('Launch Site Map — Success (green) vs Failure (red)',
                            style={'margin': '0 0 10px 0', 'fontSize': 18}),
                    html.P('Green = successful landing · Red = failed. Change the site to recenter the map.',
                           style={'color': THEME['muted'], 'fontSize': 13, 'margin': '0 0 10px 0'}),
                    html.Iframe(id='launch-site-map', srcDoc='',
                                style={'width': '100%', 'height': '500px', 'border': 'none',
                                       'borderRadius': '10px', 'backgroundColor': '#fff'}),
                ]),
                # Charts
                html.Div(style=CARD_STYLE, children=[
                    html.Div(dcc.Graph(id='success-pie-chart', style={'height': '380px'},
                                       responsive=True, config={'responsive': True})),
                ]),
                html.Div(style=CARD_STYLE, children=[
                    html.H3('Payload vs Landing Success',
                            style={'margin': '0 0 4px 0', 'fontSize': 18}),
                    html.P('Y axis: 1 = success, 0 = failure. Colored by booster version.',
                           style={'color': THEME['muted'], 'fontSize': 13, 'margin': '0 0 6px 0'}),
                    html.Div(dcc.Graph(id='success-payload-scatter-chart', style={'height': '480px'},
                                       responsive=True, config={'responsive': True})),
                ]),
                html.Div('Historical SpaceX + Wikipedia data · SVM model 87.8% (exploratory, not operational).',
                         style={'textAlign': 'center', 'color': THEME['muted'], 'fontSize': 12}),
            ],
        ),
    ],
)

# TASK 2:
# Add a callback function for `site-dropdown` as input, `success-pie-chart` as output
@app.callback( Output(component_id='success-pie-chart', component_property='figure'),
               Input(component_id='site-dropdown', component_property='value'))
def get_pie_chart(launch_site):
    if launch_site == 'All Sites':
        site_counts = spacex_df.groupby('Launch Site')['class'].sum().reset_index(name='Successful launches')
        fig = px.pie(site_counts,
                     values='Successful launches',
                     names='Launch Site',
                     title='Total Success Launches by Site',
                     hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Bold)
    else:
        site_data = spacex_df[spacex_df['Launch Site'] == launch_site].copy()
        site_data['Landing status'] = site_data['class'].map({0: 'Failure', 1: 'Success'})
        status_counts = site_data['Landing status'].value_counts().rename_axis('Landing status').reset_index(name='Launches')
        fig = px.pie(status_counts,
                     values='Launches',
                     names='Landing status',
                     title='Total Success Launches for Site {}'.format(launch_site),
                     hole=0.4,
                     color='Landing status',
                     color_discrete_map={'Success': THEME['success'], 'Failure': THEME['failure']})
    return style_fig(fig, fig.layout.title.text)

# TASK 4:
# Add a callback function for `site-dropdown` and `payload-slider` as inputs, `success-payload-scatter-chart` as output
@app.callback( Output(component_id='success-payload-scatter-chart', component_property='figure'),
              [Input(component_id='site-dropdown', component_property='value'),
               Input(component_id='payload-slider',component_property='value')])
def get_payload_chart(launch_site, payload_mass):
    low, high = payload_mass[0], payload_mass[1]
    
    if launch_site == 'All Sites':
        mask = spacex_df['Payload Mass (kg)'].between(low, high)
        plot_df = spacex_df[mask]
        title = 'Correlation Between Payload and Success for All Sites'
    else:
        site_mask = (spacex_df['Launch Site'] == launch_site)
        mask = spacex_df[site_mask]['Payload Mass (kg)'].between(low, high)
        plot_df = spacex_df[site_mask][mask]
        title = f'Correlation Between Payload and Success for Site {launch_site}'
    
    if len(plot_df) == 0:
        return style_fig(px.scatter(title=title + ' (No data in range)'), title + ' (No data in range)')

    fig = px.scatter(
        plot_df,
        x='Payload Mass (kg)',
        y='class',
        color='Booster Version',
        hover_data=['Launch Site'],
        title=title,
        opacity=0.85,
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig.update_traces(marker={'size': 11, 'line': {'width': 1, 'color': 'white'}})
    fig.update_yaxes(tickvals=[0, 1], ticktext=['Failure (0)', 'Success (1)'])
    fig = style_fig(fig, title)
    # Fix overlap: with 7+ booster versions the horizontal legend wraps over
    # the X-axis title. Push the legend further down and reserve bottom margin.
    fig.update_layout(
        margin={'l': 50, 'r': 30, 't': 60, 'b': 140},
        legend={'orientation': 'h', 'yanchor': 'top', 'y': -0.3, 'xanchor': 'center', 'x': 0.5},
        xaxis={'title': {'text': 'Payload Mass (kg)', 'standoff': 12}},
    )
    return fig


# TASK 5: Add a callback for the launch site map
@app.callback(
    Output(component_id='launch-site-map', component_property='srcDoc'),
    Input(component_id='site-dropdown', component_property='value')
)
def update_launch_map(launch_site):
    site_map = create_launch_map(launch_site)
    return site_map._repr_html_()


# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8051))
    app.run(host='0.0.0.0', port=port)

    

