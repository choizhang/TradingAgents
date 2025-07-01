from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "google"  # Use a different model
config["backend_url"] = "https://generativelanguage.googleapis.com/v1"  # Use a different backend
config["deep_think_llm"] = "gemini-2.5-flash"  # Use a different model
config["quick_think_llm"] = "gemini-2.5-flash"  # Use a different model
config["max_debate_rounds"] = 1  # Increase debate rounds
config["online_tools"] = True  # Enable online tools
config["proxies"] = {
    "http://": "http://127.0.0.1:7890",
    "https://": "http://127.0.0.1:7890",
} # Configure your proxy here if needed

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2025-06-23")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
