import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import seaborn as sns
import utils
import altair as alt



st.set_page_config(
    page_title="Cars Dashboard - Models Insights",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
    )

alt.themes.enable("dark")


total_cars, df = utils.process_data()

current_year = datetime.now().year
year_min = current_year - 5
year_max = current_year

# In your main page or wherever selections are made
if 'selected_origin' not in st.session_state:
    car_origin_list = list(df.car_origin.unique())[::1]
    st.session_state.selected_origin = car_origin_list


if 'selected_years' not in st.session_state:
    st.session_state.selected_years = (year_min, year_max)


def update_origins():
    st.session_state.selected_origin = st.session_state.origin_selector

def update_years():
    st.session_state.selected_years = st.session_state.year_selector


with st.sidebar:
    #car origin selections
    car_origin_list = list(df.car_origin.unique())[::1]
    selected_origin = st.multiselect('Select an Origin', car_origin_list, default=st.session_state.selected_origin, on_change=update_origins, key='origin_selector')




df = df[(df['car_origin'].isin(selected_origin))]


def get_top_models_per_brand_year(df):
    # Group by brand, year, model and aggregate
    grouped = df.groupby(['brand', 'year', 'model'])['count'].sum().reset_index()
    
    # Get top 5 models per brand per year
    top_models = grouped.sort_values('count', ascending=False).groupby(['brand','year']).head(5)
    
    return top_models

#top_models = get_top_models_per_brand_year(df)

# Filter years
years_range = list(range(year_min, year_max))
df_filtered = df[df['year'].isin(years_range)]
top_models_df = get_top_models_per_brand_year(df_filtered)

# 1- plotly
def plot_top_models_plotly(year_range):
   # Filter data for selected years
   df_year_filtered = top_models_df[
       (top_models_df['year'] >= year_range[0]) & 
       (top_models_df['year'] <= year_range[1])
   ].sort_values('year', ascending=False)
   
   fig = px.bar(
       df_year_filtered,
       x='model',
       y='count',
       color='brand',
       facet_col='year',
       facet_col_wrap=3,
       title=f'Top 5 Models by Brand ({year_range[0]}-{year_range[1]})',
       height=800,
       category_orders={'year': sorted(df_year_filtered['year'].unique(), reverse=True)}
   )
   
   fig.update_xaxes(tickangle=45)
   return fig

def top_5_models_sunburst(year_range):
    # Prepare data for top 5 models
    df_year_filtered = top_models_df[
       (top_models_df['year'] >= year_range[0]) & 
       (top_models_df['year'] <= year_range[1])
   ].sort_values('year', ascending=False)
    
    # Create sunburst chart
    fig = px.sunburst(
        df_year_filtered, 
        path=['brand', 'year', 'model'], 
        values='count',
        title='Top 5 Models Hierarchy'
    )

    # Customize layout to increase size
    fig.update_layout(
        width=1000,  # Increase width
        height=1000,  # Increase height
        title_font_size=20,
        title_x=0.5,  # Center the title
        margin=dict(t=50, l=0, r=0, b=0)  # Adjust margins
    )
    
    return fig

# 3. Using Plotly - Table
def create_styled_table(year_range):
    df_year_filtered = top_models_df[
       (top_models_df['year'] >= year_range[0]) & 
       (top_models_df['year'] <= year_range[1])
   ].sort_values('year', ascending=False)
    
    # Pivot the data for table format
    table_data = df_year_filtered.pivot_table(
        index=['brand', 'model'],
        columns='year',
        values='count',
        aggfunc='sum'
    ).fillna(0)
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['Brand', 'Model'] + list(table_data.columns),
            align='left',
            font=dict(size=12)
        ),
        cells=dict(
            values=[table_data.index.get_level_values(0),
                   table_data.index.get_level_values(1)] + 
                   [table_data[col] for col in table_data.columns],
            align='left',
            font=dict(size=11)
        )
    )])
    
    fig.update_layout(
        title=f'Top 5 Models by Brand ({year_range[0]}-{year_range[1]})',
        height=800
    )
    return fig

#fig_top_models_plotly = plot_top_models_plotly()
#fig_top_models_table = create_styled_table()


viz_type = st.radio(
    "Select Visualization Type",
    ["Bar Chart", "Table"]
)

# Create a narrower column for the slider
col1, col2, col3 = st.columns([1, 2, 1])  # 1:2:1 ratio

with col2:
    selected_years = st.slider(
        'Select Year Range',
        min_value=year_min,
        max_value=year_max,
        value=st.session_state.selected_years,
        key='year_selector',
        on_change=update_years
    )

if viz_type == "Bar Chart":
    #st.plotly_chart(plot_top_models_plotly(selected_years), use_container_width=True)
    st.plotly_chart(top_5_models_sunburst(selected_years), use_container_width=True)
else:
    st.plotly_chart(create_styled_table(selected_years), use_container_width=True)