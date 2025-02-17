import pandas as pd
from scipy import stats

def process_data(file='cars_202501140825.csv'):
    df = pd.read_csv(file)

    # Define car origins
    german_brands = ['bmw', 'porsche', 'mercedes', 'volkswagen']
    american_brands = ['chevrolet', 'dodge', 'gmc', 'ford', 'jeep']
    japanese_brands = ['toyota','nissan','honda','lexus']
    chinese_brands = ['chery', 'geely', 'mg']
    korean_brands = ['kia','hyundai']
    other = ['land rover']

    # Create the car_origin column
    df['car_origin'] = df['brand'].apply(
    lambda x: 'german' if x.lower() in german_brands 
                else 'american' if x.lower() in american_brands 
                else 'japanese' if x.lower() in japanese_brands 
                else 'chinese' if x.lower() in chinese_brands 
                else 'korean' if x.lower() in korean_brands 
                else 'other'
)

    df = df[(df['price'] > 1) & (df['price'] < 100000) & (df['price'] != 1111) ]

    total_cars = df.shape[0]

    df_reshaped = df[['brand', 'model', 'color', 'year', 'car_origin','mileage', 'price']].groupby(
        ['brand', 'model','color', 'year','car_origin']
    ).agg({
        'mileage': 'median',
        'price': ['median','size']
    }).rename(columns={
        'mileage': 'median_mileage',
        'price': 'median_price',
        'size' : 'count'
    }).reset_index()

    df_reshaped.columns = ['_'.join(filter(None, col)).strip() for col in df_reshaped.columns.values]


    df_reshaped.rename(
        columns={'median_mileage_median':'median_mileage',
        'median_price_median': 'median_price',
        'median_price_count': 'count'
        },
        inplace=True
    )

    df_reshaped['median_mileage'] = df_reshaped['median_mileage'].fillna(0)

    #outliers
    
    # Iterate through each brand-year combination
    # Create a copy of the dataframe
    
    # Initialize new columns
    df_reshaped['mileage_zscore'] = 0
    df_reshaped['price_zscore'] = 0
    
    # Calculate z-scores for each brand
    for brand in df['brand'].unique():
        brand_mask = df_reshaped['brand'] == brand
        
        # Calculate z-scores for mileage
        df_reshaped.loc[brand_mask, 'mileage_zscore'] = stats.zscore(
            df_reshaped.loc[brand_mask, 'median_mileage']
        )
        
        # Calculate z-scores for price
        df_reshaped.loc[brand_mask, 'price_zscore'] = stats.zscore(
            df_reshaped.loc[brand_mask, 'median_price']
        )
    
    return total_cars, df_reshaped