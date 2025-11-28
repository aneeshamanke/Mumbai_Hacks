import datetime
import requests
import json
import wikipedia
import yfinance as yf
from duckduckgo_search import DDGS
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field, ValidationError

class Tool:
    def __init__(self, name: str, description: str, args_schema: Type[BaseModel]):
        self.name = name
        self.description = description
        self.args_schema = args_schema

    def run(self, args: Any) -> str:
        raise NotImplementedError

    def validate_args(self, args: Any) -> BaseModel:
        if isinstance(args, str):
            # Attempt to handle single string argument if the schema has only one field
            fields = self.args_schema.model_fields
            if len(fields) == 1:
                key = next(iter(fields))
                return self.args_schema(**{key: args})
            else:
                 # If it's a JSON string, try to parse it (though the agent usually gives us a dict or a direct string)
                 # For now, let's assume if it's a string and we have multiple fields, it might be an error or need parsing.
                 # But our current agent extracts "args" which can be a string.
                 pass
        
        if isinstance(args, dict):
             return self.args_schema(**args)
        
        # Fallback for single argument passed directly
        # This is a bit loose, but helps with the current agent implementation
        fields = self.args_schema.model_fields
        if len(fields) == 1:
             key = next(iter(fields))
             return self.args_schema(**{key: args})
             
        raise ValueError(f"Invalid arguments for tool {self.name}: {args}")

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query string")

class TavilySearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the internet for current events, facts, or general knowledge using Tavily. Returns detailed content.",
            args_schema=WebSearchInput
        )
        from tavily import TavilyClient
        import os
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
             raise ValueError("TAVILY_API_KEY not found in environment variables")
        self.client = TavilyClient(api_key=api_key)

    def run(self, args: Any) -> str:
        try:
            validated = self.validate_args(args)
            query = validated.query
            print(f"  [Tool] Running Tavily Search for: '{query}'")
            
            # Use search_depth="advanced" for better results
            response = self.client.search(query, search_depth="advanced", max_results=5)
            
            results = []
            for r in response.get('results', []):
                title = r.get('title', 'No Title')
                content = r.get('content', 'No Content')
                url = r.get('url', 'No URL')
                results.append(f"- **{title}**\n  {content}\n  Source: {url}")
            
            if not results:
                return "No relevant results found."
                
            return "\n\n".join(results)

        except ValidationError as e:
            return f"Argument Validation Error: {e}"
        except Exception as e:
            return f"Error performing search: {str(e)}"

class WeatherInput(BaseModel):
    city: str = Field(description="The city name")

class WeatherTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_weather",
            description="Get current weather for a specific city.",
            args_schema=WeatherInput
        )

    def run(self, args: Any) -> str:
        try:
            validated = self.validate_args(args)
            city = validated.city
            print(f"  [Tool] Getting Weather for: '{city}'")
            
            # 1. Geocoding
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            geo_response = requests.get(geo_url)
            if geo_response.status_code != 200:
                 return f"Error finding location for {city}."
            
            geo_data = geo_response.json()
            if not geo_data.get("results"):
                return f"Could not find location: {city}"
                
            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            name = location["name"]
            country = location.get("country", "")

            # 2. Weather Data
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&wind_speed_unit=kmh"
            weather_response = requests.get(weather_url)
            
            if weather_response.status_code != 200:
                return f"Error fetching weather data for {name}."
                
            weather_data = weather_response.json()
            current = weather_data.get("current", {})
            temp = current.get("temperature_2m")
            humidity = current.get("relative_humidity_2m")
            wind = current.get("wind_speed_10m")
            code = current.get("weather_code")
            
            # WMO Weather interpretation codes (https://open-meteo.com/en/docs)
            weather_codes = {
                0: "Clear sky",
                1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
                77: "Snow grains",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                85: "Slight snow showers", 86: "Heavy snow showers",
                95: "Thunderstorm",
                96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }
            condition = weather_codes.get(code, "Unknown")
            
            return f"Weather in {name}, {country}: {condition}, Temperature: {temp}°C, Humidity: {humidity}%, Wind Speed: {wind} km/h"

        except ValidationError as e:
            return f"Argument Validation Error: {e}"
        except Exception as e:
            return f"Error getting weather: {e}"

class WikipediaInput(BaseModel):
    query: str = Field(description="The topic to search for on Wikipedia")

class WikipediaTool(Tool):
    def __init__(self):
        super().__init__(
            name="wikipedia",
            description="Get a concise summary of a topic from Wikipedia. Use this for factual questions about people, places, history, or concepts.",
            args_schema=WikipediaInput
        )

    def run(self, args: Any) -> str:
        try:
            validated = self.validate_args(args)
            query = validated.query
            print(f"  [Tool] Searching Wikipedia for: '{query}'")
            
            # Get summary (limit to 3 sentences for brevity)
            # Get page object to access URL
            page = wikipedia.page(query, auto_suggest=False)
            summary = page.summary
            # Limit summary length manually since we are using page object
            summary = ". ".join(summary.split(". ")[:10]) + "."
            return f"Wikipedia Summary for '{query}':\n{summary}\nSource: {page.url}"
            
        except wikipedia.exceptions.DisambiguationError as e:
            return f"Ambiguous query. Possible options: {e.options[:5]}"
        except wikipedia.exceptions.PageError:
            return f"Page not found for '{query}'."
        except ValidationError as e:
            return f"Argument Validation Error: {e}"
        except Exception as e:
            return f"Error searching Wikipedia: {e}"

class NewsInput(BaseModel):
    query: str = Field(description="The news topic to search for")
    days: int = Field(default=3, description="Number of past days to search (default: 3)")

class NewsTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_news",
            description="Get the latest news articles for a topic. Use this for current events, sports scores, or recent developments.",
            args_schema=NewsInput
        )
        from tavily import TavilyClient
        import os
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
             raise ValueError("TAVILY_API_KEY not found in environment variables")
        self.client = TavilyClient(api_key=api_key)

    def run(self, args: Any) -> str:
        try:
            validated = self.validate_args(args)
            query = validated.query
            days = validated.days
            print(f"  [Tool] Searching News for: '{query}' (Last {days} days)")
            
            # Use topic="news" for dedicated news search
            response = self.client.search(query, topic="news", days=days, max_results=5)
            
            results = []
            for r in response.get('results', []):
                title = r.get('title', 'No Title')
                content = r.get('content', 'No Content')
                url = r.get('url', 'No URL')
                # Tavily news results often have a 'published_date' or similar, but 'content' is key
                results.append(f"- **{title}**\n  {content}\n  Source: {url}")
            
            if not results:
                return f"No news found for '{query}' in the last {days} days."
                
            return "Latest News:\n" + "\n\n".join(results)

        except ValidationError as e:
            return f"Argument Validation Error: {e}"
        except Exception as e:
            return f"Error fetching news: {str(e)}"

class CalculatorInput(BaseModel):
    expression: str = Field(description="The math expression to evaluate (e.g., '25 * 4')")

class CalculatorTool(Tool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Evaluate a mathematical expression.",
            args_schema=CalculatorInput
        )

    def run(self, args: Any) -> str:
        try:
            validated = self.validate_args(args)
            expression = validated.expression
            print(f"  [Tool] Calculating: '{expression}'")
            allowed_chars = "0123456789+-*/(). "
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression."
            result = eval(expression, {"__builtins__": None}, {})
            return f"Result: {result}"
        except ValidationError as e:
            return f"Argument Validation Error: {e}"
        except Exception as e:
            return f"Error calculating: {e}"

class TimeInput(BaseModel):
    pass

class TimeTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_time",
            description="Get the current local time.",
            args_schema=TimeInput
        )

    def run(self, args: Any = None) -> str:
        print(f"  [Tool] Getting Current Time")
        now = datetime.datetime.now()
        return f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

class StockPriceInput(BaseModel):
    ticker: str = Field(description="The stock ticker symbol (e.g., 'AAPL')")

class StockPriceTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_stock_price",
            description="Get the current stock price for a given ticker symbol.",
            args_schema=StockPriceInput
        )

    def run(self, args: Any) -> str:
        try:
            validated = self.validate_args(args)
            ticker = validated.ticker
            print(f"  [Tool] Getting Stock Price for: '{ticker}'")
            ticker = ticker.strip().upper()
            # Helper to fetch price
            def fetch_price(t):
                try:
                    stock = yf.Ticker(t)
                    # fast_info is often faster/more reliable than info for price
                    price = None
                    if hasattr(stock, 'fast_info'):
                        try:
                            price = stock.fast_info.last_price
                        except:
                            pass
                    
                    if price is None:
                         price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
                    
                    currency = stock.info.get('currency', 'USD')
                    return price, currency
                except Exception as e:
                    print(f"  [Tool] Error fetching {t}: {e}")
                    return None, None

            price, currency = fetch_price(ticker)
            
            # If not found, try Indian suffixes
            if not price:
                for suffix in ['.NS', '.BO']:
                    print(f"  [Tool] Retrying with suffix: {suffix}")
                    p, c = fetch_price(ticker + suffix)
                    if p:
                        price = p
                        currency = c
                        ticker = ticker + suffix
                        break
            
            if price:
                return f"The current price of {ticker} is {price} {currency}."
            else:
                return f"Could not fetch price for {ticker}. Check if the ticker is correct."
        except ValidationError as e:
            return f"Argument Validation Error: {e}"
        except Exception as e:
            return f"Error getting stock price: {e}"
