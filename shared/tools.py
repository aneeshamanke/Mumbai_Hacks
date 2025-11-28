import datetime
import requests
import yfinance as yf
from ddgs import DDGS
from pydantic import BaseModel, Field, ValidationError
from typing import Type, Any, Dict

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

class WebSearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the internet for current events, facts, or general knowledge.",
            args_schema=WebSearchInput
        )

    def run(self, args: Any) -> str:
        try:
            validated = self.validate_args(args)
            query = validated.query
            print(f"  [Tool] Running Web Search for: '{query}'")
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if not results:
                    return "No results found."
                
                formatted_results = []
                for r in results:
                    formatted_results.append(f"- {r['title']}: {r['body']} ({r['href']})")
                return "\n".join(formatted_results)
        except ValidationError as e:
            return f"Argument Validation Error: {e}"
        except Exception as e:
            return f"Error performing search: {e}"

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
            city = city.strip("? ")
            url = f"https://wttr.in/{city}?format=%C+%t+%w"
            response = requests.get(url)
            if response.status_code == 200:
                return f"Weather in {city}: {response.text.strip()}"
            else:
                return f"Could not get weather for {city}."
        except ValidationError as e:
            return f"Argument Validation Error: {e}"
        except Exception as e:
            return f"Error getting weather: {e}"

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
            stock = yf.Ticker(ticker)
            price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
            currency = stock.info.get('currency', 'USD')
            if price:
                return f"The current price of {ticker} is {price} {currency}."
            else:
                return f"Could not fetch price for {ticker}. Check if the ticker is correct."
        except ValidationError as e:
            return f"Argument Validation Error: {e}"
        except Exception as e:
            return f"Error getting stock price: {e}"
