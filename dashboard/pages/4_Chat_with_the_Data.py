import pandas as pd
from langchain_community.llms.ollama import Ollama
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
import streamlit as st


class DataFrameQuerySystem:
    def __init__(self, df: pd.DataFrame):
        """Initialize the query system with a pandas DataFrame"""
        self.df = df
        self.agent = self._create_agent()

    def _create_agent(self):
        """Create a Langchain pandas DataFrame agent"""
        llm = Ollama(
            base_url='http://localhost:11434',
            model="mistral-nemo:12b",
            temperature=0.2,
            num_ctx=6000
        )

        return create_pandas_dataframe_agent(
            llm=llm,
            df=self.df,
            agent_type="zero-shot-react-description",
            verbose=True,
            max_iterations=20,
            allow_dangerous_code=True,
            prefix="""You are a data analyst expert working with a car dataset pandas DataFrame. 
            After performing your analysis, return ONLY the final result without any additional text.
            Familiarize yourself with the columns and their meanings before any filtering.
            
            When filtering data:
            1. Always use & for AND operations
            2. Use | for OR operations
            3. Use parentheses to group conditions
            4. Don't replace spaces with underscores
            5. If the question contains "how many" you should return the number of rows
            
            Format your responses:
            1. Prices should be in KWD with commas
            2. Percentages should have % symbol
            3. Round numbers appropriately
            
            Available columns:
            - brand: car manufacturer
            - model: car model
            - year: manufacturing year
            - price: price in KWD
            - mileage: mileage of the car
            
            IMPORTANT: Return ONLY the final answer without any explanation or working."""
        )

    def _extract_direct_response(self, response: str) -> str:
        """Clean and format the response"""
        if response:
            # Remove code blocks if present
            if "```" in response:
                response = response.split("```")[0]
            
            # Remove thought process if present
            if "Thought:" in response:
                response = response.split("Thought:")[0]
                
            return response.strip()
        return "No response generated"
        '''
        # Remove common prefixes
        prefixes_to_remove = [
            "Answer:", 
            "Response:", 
            "Final answer:", 
            "Result:",
            "Here's the",
            "The result is",
            "I calculated",
            "Based on"
        ]
        
        response = response.strip()
        for prefix in prefixes_to_remove:
            if response.lower().startswith(prefix.lower()):
                response = response[len(prefix):].strip()
        
        return response.strip()
'''
    def query(self, question: str) -> str:
        """Process a question and return the answer"""
        try:
            formatted_question = f"""Please analyze this question about the car dataset:
            {question}
            
            Remember to:
            1. Use the exact column names from the data
            2. Format prices in KWD with commas
            3. Be precise in your calculations
            4. Return only the final numerical result or summary
            """
            
            response = self.agent.run(formatted_question)
            
            # Extract and clean the response
            cleaned_response = self._extract_direct_response(response)
            
            # If empty response, return error message
            if not cleaned_response:
                return "I couldn't generate a clear answer. Please try rephrasing your question."
                
            return cleaned_response
            
        except Exception as e:
            if "Could not parse LLM output:" in str(e):
                # Extract the actual response from the error message
                import re
                match = re.search(r'Could not parse LLM output: `(.*?)`', str(e))
                if match:
                    return match.group(1)
            
            return "I couldn't process that query. Please try rephrasing your question."

def create_streamlit_interface():
    st.title("🚗 Car Data Analysis System")
    
    st.markdown("""
    Ask specific questions about the car dataset:
    - "What is the average price of Toyota cars?"
    - "How many cars are there for each brand?"
    - "What's the average mileage for BMW models?"
    - "What's the median price for 2021 Land Cruiser?"
    """)

    try:
        # Load and preprocess data
        df = pd.read_csv('../cars_202501140825.csv')
        df = df.apply(lambda x: x.str.lower() if x.dtype == "object" else x)
        df = df.apply(lambda x: x.fillna(0) if (x.dtype == "int64" or x.dtype == "float64") else x)
        df = df[(df['price'] > 1) & (df['price'] < 100000) & (df['price'] != 1111)]
        
        # Initialize query system
        if 'query_system' not in st.session_state:
            with st.spinner('Initializing analysis system...'):
                st.session_state.query_system = DataFrameQuerySystem(df)
                st.success('System ready!')

        # Chat interface
        if prompt := st.chat_input("Ask about the car data..."):
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner('Analyzing data...'):
                    response = st.session_state.query_system.query(prompt)
                    st.markdown(response)

        # Sidebar with data preview
        with st.sidebar:
            st.subheader("Dataset Information")
            st.write(f"Total records: {len(df):,}")
            st.write("Available columns:", ", ".join(df.columns))
            
            if st.checkbox("Show Data Preview"):
                st.dataframe(df.head())
                st.write("Data Types:")
                st.write(df.dtypes)

    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    create_streamlit_interface()