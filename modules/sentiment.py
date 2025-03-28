import json
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_ollama import OllamaLLM
from config import SENTIMENT_PROMPT_TEMPLATE

class SentimentAnalyzer:
    def __init__(self):
        # Set up the Ollama model with DeepSeek R1:1.5B
        self.llm = OllamaLLM(
            model="deepseek-r1:1.5b",
            # If you need to connect to a remote Ollama instance, uncomment:
            # base_url="http://localhost:11434"
        )
        
        # Create a template for sentiment analysis with RAG
        self.template = PromptTemplate(
            input_variables=["stock_symbol", "company_name", "title", "content", "date", 
                            "current_price", "year_high", "year_low"],
            template=SENTIMENT_PROMPT_TEMPLATE
        )
        
        # Create the LLM chain
        self.chain = LLMChain(llm=self.llm, prompt=self.template)
    
    def analyze_news(self, news_articles, stock_info, stock_history):
        """Analyze sentiment of news articles using DeepSeek R1 with RAG"""
        results = []
        
        for article in news_articles:
            try:
                # Prepare the input for the LLM
                chain_input = {
                    "stock_symbol": stock_info['symbol'],
                    "company_name": stock_info['company_name'],
                    "title": article['title'],
                    "content": article['content'],
                    "date": article['date'],
                    "current_price": stock_info['current_price'],
                    "year_high": stock_info['year_high'],
                    "year_low": stock_info['year_low']
                }
                
                # Get the response from the LLM
                response = self.chain.run(chain_input)
                
                # Parse the JSON response
                try:
                    # The model might return text before or after the JSON, so we need to extract it
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = response[json_start:json_end]
                        sentiment_data = json.loads(json_str)
                    else:
                        # Handle case where JSON is not properly formatted
                        sentiment_data = {
                            "sentiment": "unknown",
                            "importance": 0,
                            "explanation": "Could not parse model response",
                            "potential_impact": "unknown"
                        }
                except json.JSONDecodeError:
                    sentiment_data = {
                        "sentiment": "unknown",
                        "importance": 0,
                        "explanation": "Could not parse model response",
                        "potential_impact": "unknown"
                    }
                
                # Add the article information to the results
                result = {
                    "article": article,
                    "sentiment_analysis": sentiment_data
                }
                
                results.append(result)
                
            except Exception as e:
                print(f"Error analyzing article {article['title']}: {e}")
                results.append({
                    "article": article,
                    "sentiment_analysis": {
                        "sentiment": "error",
                        "importance": 0,
                        "explanation": f"Error: {str(e)}",
                        "potential_impact": "unknown"
                    }
                })
        
        # Sort results by importance (high to low)
        results.sort(key=lambda x: x['sentiment_analysis'].get('importance', 0), reverse=True)
        
        return results 