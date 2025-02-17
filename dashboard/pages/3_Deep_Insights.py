import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import seaborn as sns
import utils
import altair as alt

st.set_page_config(
    page_title="Cars Dashboard - Deep Insights",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
    )

alt.themes.enable("dark")

current_year = datetime.now().year
year_min = current_year - 5
year_max = current_year

df = pd.read_csv('../carmodels_deepinsights.csv')

_, df2 = utils.process_data()

df2 = (df2['year'] >= year_min) & (df2['year'] <= year_max)


if 'single_selected_brand' not in st.session_state:
    brand_list = list(df.brand.unique())[::1]
    st.session_state.single_selected_brand = brand_list[0]

if 'single_selected_model' not in st.session_state:
    model_list = list(df[df['brand'] == st.session_state.single_selected_brand]['model'].unique())[::1]
    st.session_state.single_selected_model = model_list[0]

def update_brands():
    st.session_state.single_selected_brand = st.session_state.brand_selector
    # Update models when brand changes
    model_list = list(df[df['brand'] == st.session_state.single_selected_brand]['model'].unique())[::1]
    if model_list:
        st.session_state.single_selected_model = model_list[0]

def update_models():
     st.session_state.single_selected_model = st.session_state.model_selector

with st.sidebar:
    st.title('🚗 Cars Dashboard')

    brand_list = list(df['brand'].unique())[::1]
    model_list = list(df[df['brand'] == st.session_state.single_selected_brand]['model'].unique())[::1]

    single_selected_brand = st.selectbox(
        'Select a Brand', 
        options=brand_list, 
        index=brand_list.index(st.session_state.single_selected_brand),
        on_change=update_brands, 
        key='brand_selector'
    )
    single_selected_model = st.selectbox(
        'Select a Model', 
        options=model_list, 
        index=model_list.index(st.session_state.single_selected_model),
        on_change=update_models, 
        key='model_selector'
    )

    df_selected_brand = df[df['brand'] == single_selected_brand]
    df_selected_model = df[(df['brand'] == single_selected_brand) & (df['model'] == single_selected_model)]


def plotly_age_depr_lineplot(df):
    df_depr_lineplot = df[(df['brand'] == st.session_state.single_selected_brand) & (df['model'] == st.session_state.single_selected_model)]
    # Create the line plot
    fig = px.line(
        df_depr_lineplot, 
        x='age', 
        y='depreciation_since_prev_year', 
        title='Vehicle Depreciation by Age',
        labels={
            'age': 'Age (Years)', 
            'depreciation_since_prev_year': 'Depreciation (%)'
        },
        template='plotly_white'
    )

    fig.update_xaxes(
        dtick=1,  # This ensures only whole number ticks
        tick0=0   # Optional: start ticks from 0
    )
    
    # Customize the layout
    fig.update_layout(
        xaxis_title='Age (Years)',
        yaxis_title='Depreciation (%)',
        hovermode='closest'
    )
    
    # Add markers to the line
    fig.update_traces(
        mode='lines+markers', 
        line=dict(width=3),
        marker=dict(size=8)
    )
    
    return fig
    
# FIRST: Top row with Color Distribution and Price by Brand
col = st.columns((1,2), gap='medium')

with col[0]:
    st.plotly_chart(plotly_age_depr_lineplot(df))