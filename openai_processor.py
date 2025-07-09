import json
import pandas as pd
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

class OpenAIProcessor:
    """
    Handles OpenAI API interactions for content analysis and structured output
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def analyze_content(self, content: str, analysis_prompt: str = None) -> Dict[str, Any]:
        """
        Analyze scraped content using OpenAI
        """
        if not analysis_prompt:
            analysis_prompt = """
            Analyze the following web content and extract key information. 
            Focus on the main topics, entities, and important details.
            Return the analysis in a structured format.
            """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a content analysis expert. Provide structured, accurate analysis of web content."},
                    {"role": "user", "content": f"{analysis_prompt}\n\nContent:\n{content[:8000]}"}  # Limit content length
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return {
                'analysis': response.choices[0].message.content,
                'usage': response.usage.dict() if response.usage else None
            }
            
        except Exception as e:
            return {
                'error': f"OpenAI analysis failed: {str(e)}",
                'analysis': None
            }
    
    def extract_structured_data(self, content: str, schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract structured data from content based on a schema
        """
        if not schema:
            schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "entities": {"type": "array", "items": {"type": "string"}},
                    "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                    "topics": {"type": "array", "items": {"type": "string"}}
                }
            }
        
        prompt = f"""
        Extract structured data from the following content according to this JSON schema:
        {json.dumps(schema, indent=2)}
        
        Return ONLY valid JSON that matches the schema exactly.
        
        Content:
        {content[:6000]}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data extraction expert. Return only valid JSON that matches the provided schema."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            result = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                parsed_data = json.loads(result)
                return {
                    'structured_data': parsed_data,
                    'raw_response': result,
                    'usage': response.usage.dict() if response.usage else None
                }
            except json.JSONDecodeError:
                return {
                    'error': 'Failed to parse JSON response',
                    'raw_response': result,
                    'structured_data': None
                }
                
        except Exception as e:
            return {
                'error': f"OpenAI extraction failed: {str(e)}",
                'structured_data': None
            }
    
    def generate_table_data(self, content: str, table_columns: List[str] = None) -> Dict[str, Any]:
        """
        Generate table-formatted data from content
        """
        if not table_columns:
            table_columns = ["Title", "Description", "Category", "Keywords", "Sentiment"]
        
        prompt = f"""
        Extract information from the following content and format it as a table with these columns:
        {', '.join(table_columns)}
        
        Return the data in JSON format as an array of objects, where each object represents a row with the specified columns.
        
        Content:
        {content[:6000]}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data extraction expert. Extract table data from content and return it as JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content.strip()
            
            try:
                table_data = json.loads(result)
                if isinstance(table_data, list):
                    return {
                        'table_data': table_data,
                        'columns': table_columns,
                        'row_count': len(table_data),
                        'usage': response.usage.dict() if response.usage else None
                    }
                else:
                    return {
                        'error': 'Response is not a list/array',
                        'raw_response': result,
                        'table_data': None
                    }
                    
            except json.JSONDecodeError:
                return {
                    'error': 'Failed to parse JSON response',
                    'raw_response': result,
                    'table_data': None
                }
                
        except Exception as e:
            return {
                'error': f"OpenAI table generation failed: {str(e)}",
                'table_data': None
            }
    
    def compare_content(self, content1: str, content2: str) -> Dict[str, Any]:
        """
        Compare two pieces of content and find similarities/differences
        """
        prompt = f"""
        Compare the following two pieces of content and provide a structured analysis:
        
        Content 1:
        {content1[:3000]}
        
        Content 2:
        {content2[:3000]}
        
        Analyze similarities, differences, and key insights. Return as JSON with fields:
        - similarity_score (0-1)
        - common_topics (array)
        - unique_to_content1 (array)
        - unique_to_content2 (array)
        - key_differences (array)
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a content comparison expert. Provide structured comparison analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            result = response.choices[0].message.content.strip()
            
            try:
                comparison_data = json.loads(result)
                return {
                    'comparison': comparison_data,
                    'usage': response.usage.dict() if response.usage else None
                }
            except json.JSONDecodeError:
                return {
                    'error': 'Failed to parse comparison JSON',
                    'raw_response': result,
                    'comparison': None
                }
                
        except Exception as e:
            return {
                'error': f"OpenAI comparison failed: {str(e)}",
                'comparison': None
            }
    
    def save_to_csv(self, table_data: List[Dict[str, Any]], filename: str = "scraped_data.csv") -> str:
        """
        Save table data to CSV file
        """
        try:
            df = pd.DataFrame(table_data)
            df.to_csv(filename, index=False)
            return f"Data saved to {filename}"
        except Exception as e:
            return f"Failed to save CSV: {str(e)}"
    
    def save_to_json(self, data: Dict[str, Any], filename: str = "scraped_data.json") -> str:
        """
        Save data to JSON file
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return f"Data saved to {filename}"
        except Exception as e:
            return f"Failed to save JSON: {str(e)}" 