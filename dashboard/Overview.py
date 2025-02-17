# chroma run --host 0.0.0.0 --port 8000
# streamlit run Overview.py

import streamlit as st
import utils
from datetime import datetime
import plotly.express as px
import altair as alt



st.set_page_config(
    page_title="Cars Dashboard",
    page_icon="🚗",
    layout="wide"
)

alt.themes.enable("dark")

current_year = datetime.now().year

st.title("Welcome to Cars Dashboard")
#st.sidebar.success("Select a page above.")

total_cars, df_reshaped = utils.process_data()

total_brands = len(list(df_reshaped.brand.unique()))

st.markdown('#### Total cars: ' + str(total_cars))

st.markdown('#### Total brands: ' + str(total_brands))
#st.markdown('<br>', unsafe_allow_html=True)
#st.markdown('#### Please select a page from the side bar for more insights.')

# 1- current year, then 4 previous years (2021-2024):
#   * top 5 models for each model year (or total see which makes more sense)
#   * insights on pricing by brand
#   * insights on price distribution by brand represented in a scatter plot: 
#       size of dot = count, 
#       x-axis: brand, 
#       y-axis: median price
#   * same as above but with mileage
# rag on top of table data, generate graphs from it


# In your main page or wherever selections are made
if 'selected_origin' not in st.session_state:
    car_origin_list = list(df_reshaped.car_origin.unique())[::1]
    st.session_state.selected_origin = car_origin_list

if 'remove_outliers' not in st.session_state:
    st.session_state.remove_outliers = False

def update_origins():
    st.session_state.selected_origin = st.session_state.origin_selector

def update_outliers():
    st.session_state.remove_outliers = st.session_state.outliers



with st.sidebar:
    #car origin selections
    car_origin_list = list(df_reshaped.car_origin.unique())[::1]
    selected_origin = st.multiselect('Select an Origin', car_origin_list, default=st.session_state.selected_origin, on_change=update_origins, key='origin_selector')
    remove_outliers = st.checkbox('Remove Outliers', value=st.session_state.remove_outliers,on_change=update_outliers, key='outliers' )




if remove_outliers:
    df_reshaped = df_reshaped[
        (abs(df_reshaped['mileage_zscore']) <= 5) & 
        (abs(df_reshaped['price_zscore']) <= 5)
    ]
else:
    df_filtered = df_reshaped.copy()

df_reshaped = df_reshaped[(df_reshaped['year'] >= current_year - 10) 
                          & (df_reshaped['year'] <= current_year) 
                          & (df_reshaped['car_origin'].isin(selected_origin))]

pivot_table = df_reshaped.pivot_table(
    values='count',
    index='brand',
    columns='year',
    aggfunc='sum'
).fillna(0)

# Sort columns in descending order (most recent year first)
pivot_table = pivot_table.sort_index(axis=1, ascending=False).round(0)

styled_df = pivot_table.style.background_gradient(
    cmap='Greens',
    axis=None,
    vmin=pivot_table.min().min(),  # Global minimum for consistent scale
    vmax=pivot_table.max().max(),  # Global maximum for consistent scale
    text_color_threshold=0.5  # Adjust text color based on background
).format("{:.0f}")

# Display in Streamlit
st.dataframe(
    styled_df,
    column_config={
        "_index": "Brand"
    },
    use_container_width=True
)





# Round mileage values first
df_reshaped['median_mileage'] = df_reshaped['median_mileage'].round(-3)  # Round to nearest thousand

# Reaggregate data with rounded mileage
df_aggregated = df_reshaped.groupby(['brand', 'median_mileage', 'median_price'])['count'].sum().reset_index()

# Get top 10 brands by total count
top_10_brands = df_reshaped.groupby('brand')['count'].sum().nlargest(10)
brand_order = list(top_10_brands.index) 

# Filter dataframe for top 10 brands
df_top10 = df_reshaped[df_reshaped['brand'].isin(brand_order)]

# Create scatter plot
fig = px.scatter(
   df_top10,
   x='median_mileage',
   y='median_price',
   size='count',
   hover_data=['brand', 'year', 'count'],
   color='brand',
   category_orders={'brand': brand_order},
   labels={
       'median_mileage': 'Mileage',
       'median_price': 'Price',
       'count': 'Count'
   },
   title='Price vs Mileage for Top 10 Brands (dot size represents count)'
)

# Update layout with custom x-axis ticks
fig.update_layout(
   height=600,
   width=800,
   showlegend=True,
   xaxis=dict(
       dtick=50000,
       tickformat=',d',
       range=[0, 400000 * 1.1],  # Start at 0, end slightly above max
       zeroline=True
   ),
   yaxis=dict(
       range=[0, df_top10['median_price'].max() * 1.1],  # Start at 0, end slightly above max
       zeroline=True
   )
)

# Display in Streamlit
st.plotly_chart(fig, use_container_width=True)


