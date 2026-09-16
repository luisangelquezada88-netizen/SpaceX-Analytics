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
app = dash.Dash(__name__)
server = app.server  # Expuesto para gunicorn / Render (producción)

# Nota perf: NO pre-renderizamos el mapa Folium al importar.
# Antes hacíamos create_launch_map('All Sites')._repr_html_() aquí y
# retrasaba 2-5s el arranque (healthcheck de Render). Ahora el iframe
# arranca vacío y el callback update_launch_map lo rellena al cargar la página.

# Create an app layout
app.layout = html.Div(children=[html.H1('SpaceX Launch Records Dashboard',
                                        style={'textAlign': 'center', 'color': '#503D36',
                                               'font-size': 40}),
                                # TASK 1: Add a dropdown list to enable Launch Site selection
                                # The default select value is for ALL sites
                                dcc.Dropdown(id='site-dropdown',
                                options=[
                                    {'label': 'All Sites', 'value': 'All Sites'},
                                    {'label': 'CCAFS LC-40', 'value': 'CCAFS LC-40'},
                                    {'label': 'VAFB SLC-4E', 'value': 'VAFB SLC-4E'},
                                    {'label': 'KSC LC-39A', 'value': 'KSC LC-39A'},
                                    {'label': 'CCAFS SLC-40', 'value': 'CCAFS SLC-40'}
                                ],
                                placeholder='Select a Launch Site Here',
                                value='All Sites',
                                searchable=True
                                ),
                                html.Br(),

                                # Launch Site Map with Success/Failure Clusters
                                html.H3('Launch Site Map - Success/Failure Clusters', style={'textAlign': 'center'}),
                                html.Iframe(id='launch-site-map', srcDoc='',
                                           style={'width': '100%', 'height': '500px', 'border': 'none'}),
                                html.Br(),

                                # TASK 2: Add a pie chart to show the total successful launches count for all sites
                                # If a specific launch site was selected, show the Success vs. Failed counts for the site
                                html.Div(dcc.Graph(id='success-pie-chart')),
                                html.Br(),

                                html.P("Payload range (Kg):"),
                                # TASK 3: Add a slider to select payload range
                                dcc.RangeSlider(id='payload-slider',
                                min=0,
                                max=10000,
                                step=1000,
                                marks={i: '{}'.format(i) for i in range(0, 10001, 1000)},
                                value=[min_payload, max_payload]),

                                # TASK 4: Add a scatter chart to show the correlation between payload and launch success
                                html.Div(dcc.Graph(id='success-payload-scatter-chart')),
                                ])

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
                     title='Total Success Launches by Site')
    else:
        site_data = spacex_df[spacex_df['Launch Site'] == launch_site].copy()
        site_data['Landing status'] = site_data['class'].map({0: 'Failure', 1: 'Success'})
        status_counts = site_data['Landing status'].value_counts().rename_axis('Landing status').reset_index(name='Launches')
        fig = px.pie(status_counts,
                     values='Launches',
                     names='Landing status',
                     title='Total Success Launches for Site {}'.format(launch_site))
    return(fig)

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
        return px.scatter(title=title + ' (No data in range)')
    
    fig = px.scatter(
        plot_df,
        x='Payload Mass (kg)',
        y='class',
        color='Booster Version',
        hover_data=['Launch Site'],
        title=title,
        opacity=0.7
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

    

