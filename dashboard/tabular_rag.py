import pandas as pd
import chromadb
from langchain_community.llms.ollama import Ollama
from typing import Dict, List, Any
import json

class TabularRAG:
    def __init__(self, df: pd.DataFrame):
        """Initialize TabularRAG with a pandas DataFrame"""
        self.df = df
        self.collection = None

    def add_car_specific_statistics(self, contexts: List[str]) -> List[str]:
        """Add detailed car-specific statistics to the context"""
        
        # 1. Brand Analytics
        brand_stats = {
            'brand_distribution': self.df['brand'].value_counts().head(10).to_dict(),
            'total_brands': self.df['brand'].nunique()
        }
        
        # Calculate brand price stats
        brand_price_stats = {}
        for brand in self.df['brand'].unique():
            brand_data = self.df[self.df['brand'] == brand]
            brand_price_stats[brand] = {
                'mean_price': float(brand_data['price'].mean()),
                'min_price': float(brand_data['price'].min()),
                'max_price': float(brand_data['price'].max()),
                'count': len(brand_data)
            }
        brand_stats['brand_price_stats'] = brand_price_stats
        
        # Calculate brand mileage stats
        brand_mileage_stats = {}
        for brand in self.df['brand'].unique():
            brand_data = self.df[self.df['brand'] == brand]
            brand_mileage_stats[brand] = {
                'mean_mileage': float(brand_data['mileage'].mean()),
                'min_mileage': float(brand_data['mileage'].min()),
                'max_mileage': float(brand_data['mileage'].max())
            }
        brand_stats['brand_mileage_stats'] = brand_mileage_stats
        
        contexts.append(f"Brand statistics: {json.dumps(brand_stats, indent=2)}")

        # 2. Year Analysis
        if 'year' in self.df.columns:
            year_stats = {
                'year_distribution': self.df['year'].value_counts().sort_index().to_dict(),
                'newest_year': int(self.df['year'].max()),
                'oldest_year': int(self.df['year'].min()),
                'price_by_year': self.df.groupby('year')['price'].mean().round(2).to_dict(),
                'mileage_by_year': self.df.groupby('year')['mileage'].mean().round(2).to_dict()
            }
            contexts.append(f"Year statistics: {json.dumps(year_stats, indent=2)}")

            # Brand and year combinations
            brand_year_stats = {}
            for brand in self.df['brand'].unique():
                brand_data = self.df[self.df['brand'] == brand]
                if len(brand_data) > 0:
                    brand_year_stats[brand] = {
                        'years_available': sorted(brand_data['year'].unique().tolist()),
                        'most_common_year': int(brand_data['year'].mode().iloc[0]),
                        'avg_price_by_year': brand_data.groupby('year')['price'].mean().round(2).to_dict()
                    }
            contexts.append(f"Brand-Year statistics: {json.dumps(brand_year_stats, indent=2)}")

        # 3. Color Analysis
        if 'color' in self.df.columns:
            color_stats = {
                'color_distribution': self.df['color'].value_counts().head(10).to_dict(),
                'total_colors': self.df['color'].nunique()
            }
            
            # Price by color
            price_by_color = {}
            for color in self.df['color'].unique():
                color_data = self.df[self.df['color'] == color]
                price_by_color[color] = {
                    'mean_price': float(color_data['price'].mean()),
                    'count': len(color_data)
                }
            color_stats['price_by_color'] = price_by_color
            
            # Mileage by color
            color_stats['mileage_by_color'] = self.df.groupby('color')['mileage'].mean().round(2).to_dict()
            
            # Popular colors by brand
            popular_colors = {}
            for brand in self.df['brand'].unique():
                brand_data = self.df[self.df['brand'] == brand]
                popular_colors[brand] = brand_data['color'].value_counts().head(3).to_dict()
            color_stats['popular_colors_by_brand'] = popular_colors
            
            contexts.append(f"Color statistics: {json.dumps(color_stats, indent=2)}")

        # 4. Model Analysis
        if 'model' in self.df.columns:
            model_stats = {}
            
            # Models per brand
            models_per_brand = {}
            for brand in self.df['brand'].unique():
                brand_models = self.df[self.df['brand'] == brand]['model'].unique()
                models_per_brand[brand] = {
                    'total_models': len(brand_models),
                    'models': list(brand_models)
                }
            model_stats['models_per_brand'] = models_per_brand
            
            # Top models by price
            model_price_data = []
            for brand in self.df['brand'].unique():
                for model in self.df[self.df['brand'] == brand]['model'].unique():
                    model_data = self.df[(self.df['brand'] == brand) & (self.df['model'] == model)]
                    model_price_data.append({
                        'brand': brand,
                        'model': model,
                        'mean_price': float(model_data['price'].mean()),
                        'count': len(model_data)
                    })
            model_price_data = sorted(model_price_data, key=lambda x: x['mean_price'], reverse=True)[:10]
            model_stats['top_models_by_price'] = model_price_data
            
            contexts.append(f"Model statistics: {json.dumps(model_stats, indent=2)}")

        # 5. Market Segment Analysis
        price_75th = self.df['price'].quantile(0.75)
        price_25th = self.df['price'].quantile(0.25)
        
        segment_stats = {}
        for segment_name, segment_data in {
            'luxury': self.df[self.df['price'] > price_75th],
            'mid_range': self.df[(self.df['price'] >= price_25th) & (self.df['price'] <= price_75th)],
            'budget': self.df[self.df['price'] < price_25th]
        }.items():
            segment_stats[segment_name] = {
                'price_range': {
                    'min': float(segment_data['price'].min()),
                    'max': float(segment_data['price'].max()),
                    'mean': float(segment_data['price'].mean())
                },
                'top_brands': segment_data['brand'].value_counts().head(5).to_dict(),
                'avg_mileage': float(segment_data['mileage'].mean()),
                'total_listings': len(segment_data)
            }
        contexts.append(f"Market segment statistics: {json.dumps(segment_stats, indent=2)}")

        return contexts

    def prepare_dataframe_context(self) -> List[str]:
        """Convert DataFrame into contextual information"""
        contexts = []
        
        # Basic DataFrame summary
        summary = {
            'total_rows': len(self.df),
            'columns': list(self.df.columns),
            'numeric_summaries': self.df.describe().to_dict(),
            'categorical_summaries': {
                col: self.df[col].value_counts().to_dict() 
                for col in self.df.select_dtypes(include=['object']).columns
            }
        }
        contexts.append(f"DataFrame Summary: {json.dumps(summary, indent=2)}")
        
        # Add car-specific statistics
        contexts = self.add_car_specific_statistics(contexts)
        
        return contexts

    def initialize_chromadb(self, collection_name: str = "tabular_data"):
        """Initialize ChromaDB with DataFrame insights"""
        client = chromadb.HttpClient(
            host="localhost",
            port=8000,
            settings=chromadb.Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        # Reset collection if it exists
        try:
            client.delete_collection(name=collection_name)
        except:
            pass
            
        # Create new collection
        self.collection = client.create_collection(name=collection_name)
        
        # Prepare and add contexts
        contexts = self.prepare_dataframe_context()
        
        # Add to collection
        self.collection.add(
            documents=contexts,
            metadatas=[{"type": "dataframe_context"} for _ in contexts],
            ids=[f"context_{i}" for i in range(len(contexts))]
        )

    def initialize(self) -> bool:
        """Initialize the RAG system"""
        try:
            self.initialize_chromadb()
            return True
        except Exception as e:
            print(f"Error initializing TabularRAG: {e}")
            return False

    def query(self, question: str) -> str:
        """Query the RAG system with improved prompting for car data"""
        try:
            # Query the collection with more results and add debug info
            results = self.collection.query(
                query_texts=[question],
                n_results=5  # Increased from 3 to get more context
            )
            
            if not results['documents'][0]:
                return "I couldn't find relevant information to answer your question. Please try rephrasing or ask another question."
            
            # Combine all relevant contexts
            context = "\n".join(results['documents'][0])
            
            llm = Ollama(
                base_url='http://localhost:11434',
                model="mistral-nemo:12b",
                temperature=3
            )
            
            prompt = f"""You are a car data analyst. You have access to a database of car statistics and must answer questions based ONLY on the provided statistical context.

Question: {question}

Statistical Context:
{context}

Important Instructions:
1. ONLY use information from the provided context
2. If the context contains specific numbers, use those exact numbers
3. Always mention specific statistics when available
4. Format prices with $ and commas (e.g., $30,000)
5. Reference specific brands, models, or years when available
6. If you can't find relevant information in the context, say so
7. For numerical values: 
   - Round prices to 2 decimal places
   - Round mileage to whole numbers
   - Include units (dollars, miles, etc.)

Provide a direct and factual answer based on the above context:"""

            response = llm(prompt)
            
            # Add debug information if needed
            # print("Question:", question)
            # print("Context used:", context)
            # print("Response:", response)
            
            return response

        except Exception as e:
            return f"I encountered an error while processing your question: {str(e)}"