from typing import Dict, List, Any
import pandas as pd
import chromadb

def add_data_to_collection(collection, df: pd.DataFrame) -> chromadb.Collection:
    """Add data to ChromaDB collection"""
    # Convert DataFrame rows to documents and embeddings
    documents = []
    metadatas = []
    ids = []
    
    # Process each row in the DataFrame
    for idx, row in df.iterrows():
        # Create a detailed document text that includes all relevant information
        doc_text = (
            f"This is a {row['brand']} car with the following details: "
            f"Median price is ${row['median_price']:.2f}, "
            f"Median mileage is {row['median_mileage']} miles."
        )
        documents.append(doc_text)
        
        # Add metadata
        metadatas.append({
            "brand": row["brand"],
            "price": str(row["median_price"]),
            "mileage": str(row["median_mileage"])
        })
        
        # Create unique ID
        ids.append(f"doc_{idx}")
    
    # Add documents to collection in batches of 20
    batch_size = 20
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        collection.add(
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
    
    return collection

def query_collection(collection: chromadb.Collection, query_text: str, n_results: int = 5) -> Dict[str, List[Any]]:
    """Query the ChromaDB collection"""
    try:
        # Query the collection
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
        )
        
        if not results['documents'][0]:
            print("No results found for query:", query_text)
        else:
            print(f"Found {len(results['documents'][0])} results for query:", query_text)
        
        return results
    except Exception as e:
        print(f"Error querying collection: {e}")
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

def create_chroma_collection(df: pd.DataFrame, collection_name: str = "car_data") -> chromadb.Collection:
    """Create a new ChromaDB collection and populate it with data"""
    client = chromadb.HttpClient(
        host="localhost",
        port=8000,
        settings=chromadb.Settings(
            allow_reset=True,
            anonymized_telemetry=False
        )
    )
    
    try:
        client.delete_collection(name=collection_name)
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Car data embeddings"}
    )
    
    populated_collection = add_data_to_collection(collection, df)
    
    return populated_collection