import datetime
import requests
import yfinance as yf
from ddgs import DDGS

class Tool:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def run(self, arg):
        raise NotImplementedError

class WebSearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the internet for current events, facts, or general knowledge. Argument: The search query string."
        )

    def run(self, query: str) -> str:
        print(f"  [Tool] Running Web Search for: '{query}'")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if not results:
                    return "No results found."
                
                formatted_results = []
                for r in results:
                    formatted_results.append(f"- {r['title']}: {r['body']} ({r['href']})")
                return "\n".join(formatted_results)
        except Exception as e:
            return f"Error performing search: {e}"

class WeatherTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_weather",
            description="Get current weather for a specific city. Argument: The city name."
        )

    def run(self, city: str) -> str:
        print(f"  [Tool] Getting Weather for: '{city}'")
        try:
            city = city.strip("? ")
            url = f"https://wttr.in/{city}?format=%C+%t+%w"
            response = requests.get(url)
            if response.status_code == 200:
                return f"Weather in {city}: {response.text.strip()}"
            else:
                return f"Could not get weather for {city}."
        except Exception as e:
            return f"Error getting weather: {e}"

class CalculatorTool(Tool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Evaluate a mathematical expression. Argument: The math expression string (e.g., '25 * 4')."
        )

    def run(self, expression: str) -> str:
        print(f"  [Tool] Calculating: '{expression}'")
        try:
            allowed_chars = "0123456789+-*/(). "
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression."
            result = eval(expression, {"__builtins__": None}, {})
            return f"Result: {result}"
        except Exception as e:
            return f"Error calculating: {e}"

class TimeTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_time",
            description="Get the current local time. Argument: None (ignore)."
        )

    def run(self, _=None) -> str:
        print(f"  [Tool] Getting Current Time")
        now = datetime.datetime.now()
        return f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

class StockPriceTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_stock_price",
            description="Get the current stock price for a given ticker symbol. Argument: The stock ticker (e.g., 'AAPL', 'TSLA', 'GOOG')."
        )

    def run(self, ticker: str) -> str:
        print(f"  [Tool] Getting Stock Price for: '{ticker}'")
        try:
            ticker = ticker.strip().upper()
            stock = yf.Ticker(ticker)
            price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
            currency = stock.info.get('currency', 'USD')
            if price:
                return f"The current price of {ticker} is {price} {currency}."
            else:
                return f"Could not fetch price for {ticker}. Check if the ticker is correct."
        except Exception as e:
            return f"Error getting stock price: {e}"
