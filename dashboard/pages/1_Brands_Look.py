import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import utils

st.set_page_config(
    page_title="Cars Dashboard - Brand Insights",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
    )

#st.title("Overview")
alt.themes.enable("dark")


total_cars, df_reshaped = utils.process_data()



# Calculate total count for each brand and color
color_counts = df_reshaped.groupby(['brand', 'color'])['color'].count().reset_index(name='color_count')

# Calculate total count for each brand (for percentage calculation)
brand_totals = df_reshaped.groupby('brand')['color'].count().reset_index(name='total_count')

# Merge to calculate percentages
color_percentages = color_counts.merge(brand_totals, on='brand')
color_percentages['percentage'] = (color_percentages['color_count'] / color_percentages['total_count'] * 100).round(2)

color_percentages = color_percentages.merge(df_reshaped[['brand']].drop_duplicates(), on='brand')


if 'selected_brand' not in st.session_state:
    brand_list = list(df_reshaped.brand.unique())[::1]
    st.session_state.selected_brand = brand_list

if 'remove_outliers' not in st.session_state:
    st.session_state.remove_outliers = False


def update_brands():
    st.session_state.selected_brand = st.session_state.brand_selector

def update_outliers():
    st.session_state.remove_outliers = st.session_state.outliers



with st.sidebar:
    st.title('🚗 Cars Dashboard')
    
    #year_list = sorted(df_reshaped.year.unique(), reverse=True)
    #selected_year = st.selectbox('Select a year', year_list, index=len(year_list)-1)
    
    #color_theme_list = ['blues', 'cividis', 'greens', 'magma', 'plasma', 'reds', 'viridis']
    #selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

    #car origin selections
    #car_origin_list = list(df_reshaped.car_origin.unique())[::1]
    #selected_origin = st.multiselect('Select an Origin', car_origin_list, default=car_origin_list)

    # Add select all button
    brand_list = list(df_reshaped.brand.unique())[::1]

    selected_brand = st.multiselect('Select a Brand', brand_list, default=st.session_state.selected_brand, on_change=update_brands, key='brand_selector')

    df_selected_brand = df_reshaped[df_reshaped['brand'].isin(selected_brand)]

    remove_outliers = st.checkbox('Remove Outliers', value=st.session_state.remove_outliers,on_change=update_outliers, key='outliers' )



#df_selected_brand = df_reshaped[df_reshaped['brand'].isin(selected_brand)] 

# Recalculate color percentages based on selected brands
if len(selected_brand) > 0:
    # Get total count for all selected brands
    color_counts = df_reshaped[df_reshaped['brand'].isin(selected_brand)].groupby(['color'])['color'].count().reset_index(name='color_count')
    #
    total_count = color_counts['color_count'].sum()
    
    # Calculate percentage out of total
    color_counts['percentage'] = (color_counts['color_count'] / total_count * 100).round(2)
    
    # Sort by percentage in descending order
    color_percentages = color_counts.sort_values('percentage', ascending=False)
else:
    # Create empty DataFrame if no brands selected
    color_percentages = pd.DataFrame(columns=['color', 'color_count', 'percentage'])

if remove_outliers:
    df_reshaped = df_reshaped[
        (abs(df_reshaped['mileage_zscore']) <= 5) & 
        (abs(df_reshaped['price_zscore']) <= 5)
    ]
else:
    df_filtered = df_reshaped.copy()


def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    #relative to the whole dataset
    '''
    heatmap = alt.Chart(input_df).mark_rect().encode(
            y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="Year", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
            x=alt.X(f'{input_x}:O', axis=alt.Axis(title="", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
            color=alt.Color(f'mean({input_color}):Q',
                             legend=None,
                             scale=alt.Scale(scheme=input_color_theme)),
            stroke=alt.value('black'),
            strokeWidth=alt.value(0.25),
        ).properties(width=900
        ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
        ) 
    # height=300
    '''
    
    # relative to xaxis
    # First create the base chart with faceting to get independent scales
    base = alt.Chart(input_df).mark_rect().encode(
    y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="Year", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
    color=alt.Color(
        'median_price:Q',
        legend=None,
        scale=alt.Scale(scheme='greens')
    ),
    tooltip=[
        alt.Tooltip('year:O', title='Year'),
        alt.Tooltip('median_price:Q', title='Price', format=',.0f')
        #alt.Tooltip('count:Q', title='Count')  # Add count to tooltip
    ],
    stroke=alt.value('black'),
    strokeWidth=alt.value(0.25)
).properties(
    width=45  # Width per facet
   ,height=600  # Height of each facet
)

    heatmap = base.facet(
    column=alt.Column('brand:O', 
        header=alt.Header(
            labelOrient='bottom',
            #labelAngle=45,
            titleOrient='bottom',
            title=None
            #,labelPadding=50  # Increased padding to move labels down
        )
    ),
        spacing=5
    ).resolve_scale(
        color='independent'
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    ).properties(
        padding={"right": 50, "bottom": 70}  # Increased bottom padding
    )


    return heatmap

def make_color_trend_chart(color_percentages):
    # Calculate dynamic height based on number of colors
    num_colors = len(color_percentages)
    height = max(300, num_colors * 30)  # Minimum height of 300px, 25px per color

    color_chart = alt.Chart(color_percentages).mark_bar(color='darkgreen').encode(
        x=alt.X('percentage:Q', 
                title='Percentage (%)',
                scale=alt.Scale(domain=[0, 100])),
        y=alt.Y('color:N', 
                title='Color',
                sort='-x',
                axis=alt.Axis(labelLimit=200)),
        tooltip=[
            alt.Tooltip('color:N', title='Color'),
            alt.Tooltip('percentage:Q', title='Percentage', format='.1f'),
            alt.Tooltip('color_count:Q', title='Count')
        ]
    ).properties(
        width=300,
        height=height  # Dynamic height
        #title='Color Distribution by Brand'
    )
    return color_chart


# Price Histogram with proper binning
price_hist = alt.Chart(df_reshaped).transform_bin(
    'price_bins',
    field='median_price',
    bin=alt.Bin(maxbins=50)  # Changed 'bins' to 'bin'
).mark_area(
    opacity=0.5,
    interpolate='step'
).encode(
    x=alt.X('price_bins:Q', title='Price'),
    y=alt.Y('count()', stack=None, title='Count'),
    tooltip=[
        alt.Tooltip('price_bins:Q', title='Price', format=',.0f'),
        alt.Tooltip('count()', title='Count')
    ]
).properties(
    height=300
)

# Mileage Histogram with proper binning
mileage_hist = alt.Chart(df_reshaped).transform_bin(
    'mileage_bins',
    field='median_mileage',
    bin=alt.Bin(maxbins=50)  # Changed 'bins' to 'bin'
).mark_area(
    opacity=0.5,
    interpolate='step'
).encode(
    x=alt.X('mileage_bins:Q', title='Mileage'),
    y=alt.Y('count()', stack=None, title='Count'),
    tooltip=[
        alt.Tooltip('mileage_bins:Q', title='Mileage', format=',.0f'),
        alt.Tooltip('count()', title='Count')
    ]
).properties(
    height=300
)

# Display them side by side

#col1, col2 = st.columns(2)
#with col1:
#    st.altair_chart(price_hist, use_container_width=True)
#with col2:
#    st.altair_chart(mileage_hist, use_container_width=True)


# FIRST: Top row with Color Distribution and Price by Brand
col = st.columns((1,2), gap='medium')
with col[0]:
    st.markdown('#### Color Distribution by Brand')
    if not color_percentages.empty:
        color_chart = make_color_trend_chart(color_percentages)
        st.altair_chart(color_chart, use_container_width=True)
    else:
        st.write("No data to display")

with col[1]:
    st.markdown('#### Price by Brand')
    heatmap = make_heatmap(df_reshaped[df_reshaped['brand'].isin(selected_brand)], 'year', 'brand', 'median_price', 'greens')
    st.altair_chart(heatmap, use_container_width=True)

# Add spacing between rows
st.markdown("<br>", unsafe_allow_html=True)

# SECOND: Bottom row with histograms
hist_cols = st.columns(2)
with hist_cols[0]:
    st.markdown('#### Price Distribution')
    if not df_selected_brand.empty:
        fig_price = px.histogram(
            df_selected_brand,
            x='median_price',
            nbins=50,
            #title='Price Distribution',
            labels={'median_price': 'Price', 'count': 'Count'},
            height=400
        )
        fig_price.update_layout(
            showlegend=False,
            margin=dict(t=30)  # Reduce top margin
        )
        st.plotly_chart(fig_price, use_container_width=True)
    else:
        st.write("No data to display")

with hist_cols[1]:
    st.markdown('#### Mileage Distribution')
    if not df_selected_brand.empty:
        fig_mileage = px.histogram(
            df_selected_brand,
            x='median_mileage',
            nbins=50,
            #title='Mileage Distribution',
            labels={'median_mileage': 'Mileage', 'count': 'Count'},
            height=400
        )
        fig_mileage.update_layout(
            showlegend=False,
            margin=dict(t=30)  # Reduce top margin
        )
        st.plotly_chart(fig_mileage, use_container_width=True)
    else:
        st.write("No data to display")