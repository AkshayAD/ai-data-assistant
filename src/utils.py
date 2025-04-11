import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Configure Gemini API
def configure_genai():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
        st.stop()
    genai.configure(api_key=api_key)

# Function to generate response from Gemini API
def get_gemini_response(prompt, persona="general", model="gemini-1.5-flash"):
    """
    Get a response from the Gemini API
    
    Args:
        prompt (str): The prompt to send to the API
        persona (str): The persona to use (manager, analyst, associate)
        model (str): The model to use (defaults to gemini-1.5-flash)
    
    Returns:
        str: The response from the API
    """
    try:
        # Configure persona-specific system instructions
        if persona == "manager":
            system_instruction = """You are an AI Data Analysis Manager. Your role is to create structured analytical plans, 
            synthesize insights, and provide clear guidance for data analysis projects. Be concise, professional, and focus 
            on creating actionable plans that address the business goals."""
        elif persona == "analyst":
            system_instruction = """You are an AI Data Analyst. Your role is to examine data, perform calculations, 
            and provide objective observations about patterns and trends. Be precise, technical, and focus on 
            extracting meaningful insights from the data."""
        elif persona == "associate":
            system_instruction = """You are an AI Senior Data Associate. Your role is to review analysis plans, 
            guide execution, define hypotheses, and formulate clear storylines for data exploration. Be strategic, 
            detail-oriented, and focus on connecting analysis to business objectives."""
        else:
            system_instruction = """You are an AI assistant helping with data analysis."""
        
        # Generate response
        model = genai.GenerativeModel(model)
        response = model.generate_content(
            [system_instruction, prompt],
            generation_config={"temperature": 0.2}
        )
        
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None

# Function to read and process CSV files
def process_csv_file(uploaded_file):
    """
    Process an uploaded CSV file
    
    Args:
        uploaded_file: The uploaded file object from Streamlit
    
    Returns:
        DataFrame: The processed pandas DataFrame
        dict: A profile of the data
    """
    try:
        # Read the CSV file
        df = pd.read_csv(uploaded_file)
        
        # Generate a basic profile of the data
        profile = {
            "columns": list(df.columns),
            "shape": df.shape,
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": df.isna().sum().to_dict(),
            "numeric_summary": {}
        }
        
        # Generate summary statistics for numeric columns
        for col in df.select_dtypes(include=['number']).columns:
            profile["numeric_summary"][col] = {
                "mean": df[col].mean(),
                "median": df[col].median(),
                "min": df[col].min(),
                "max": df[col].max()
            }
        
        return df, profile
    except Exception as e:
        st.error(f"Error processing CSV file: {str(e)}")
        return None, None

# Function to generate a data profile summary for the AI Analyst
def generate_data_profile_summary(profile):
    """
    Generate a summary of the data profile for the AI Analyst
    
    Args:
        profile (dict): The data profile
    
    Returns:
        str: A text summary of the data profile
    """
    if not profile:
        return "No data profile available."
    
    summary = f"""
    Data Profile Summary:
    - Dimensions: {profile['shape'][0]} rows × {profile['shape'][1]} columns
    - Columns: {', '.join(profile['columns'])}
    
    Data Types:
    """
    
    for col, dtype in profile['dtypes'].items():
        summary += f"- {col}: {dtype}\n"
    
    summary += "\nMissing Values:\n"
    for col, count in profile['missing_values'].items():
        if count > 0:
            summary += f"- {col}: {count} missing values ({(count/profile['shape'][0])*100:.1f}%)\n"
    
    if profile['numeric_summary']:
        summary += "\nNumeric Column Statistics:\n"
        for col, stats in profile['numeric_summary'].items():
            summary += f"- {col}: mean={stats['mean']:.2f}, median={stats['median']:.2f}, min={stats['min']:.2f}, max={stats['max']:.2f}\n"
    
    return summary
