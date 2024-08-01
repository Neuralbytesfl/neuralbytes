from openai import OpenAI
import requests
import time

# Initialize the OpenAI client with the appropriate base URL and API key
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# Initialize the conversation history with the initial prompt
history = [
    {"role": "system", "content": "Current year is 2024. We are Monitoring real-time Bitcoin data and provide summaries every minute. We want to follow the trend and identify good buys and sells based on what we are observing. Extracted data includes price, volume, 24-hour high and low, and 7-day change percentage. we have 1000 in total for this entire experiment. if you see any good time to buy or sell based on whatever indicator you think its good please do so. keep track of my balance and roi"}
]

# Function to fetch real-time data for Bitcoin from the CoinGecko API
def get_bitcoin_data():
    try:
        # Make a GET request to the CoinGecko API to fetch Bitcoin data
        response = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false")
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response and extract the Bitcoin data
            bitcoin_data = response.json()
            
            # Extract relevant data
            bitcoin_price = bitcoin_data["market_data"]["current_price"]["usd"]
            bitcoin_volume = bitcoin_data["market_data"]["total_volume"]["usd"]
            bitcoin_open = bitcoin_data["market_data"]["market_cap"]["usd"]
            bitcoin_high = bitcoin_data["market_data"]["high_24h"]["usd"]
            bitcoin_low = bitcoin_data["market_data"]["low_24h"]["usd"]
            bitcoin_7d_change = bitcoin_data["market_data"]["price_change_percentage_7d"]
            
            return {
                "price": bitcoin_price,
                "volume": bitcoin_volume,
                "open": bitcoin_open,
                "high": bitcoin_high,
                "low": bitcoin_low,
                "7d_change": bitcoin_7d_change
            }
        else:
            print(f"Failed to fetch Bitcoin data. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

# Process each real-time Bitcoin data update continuously
while True:
    # Get real-time Bitcoin data
    bitcoin_data = get_bitcoin_data()
    if bitcoin_data is not None:
        # Add the current Bitcoin data as user input to the conversation history
        history.append({"role": "user", "content": f"Bitcoin data: {bitcoin_data}"})
        
        # Get AI's response for the current Bitcoin data
        completion = client.chat.completions.create(
            model="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
            messages=history,
            temperature=0.7,
            stream=True,
        )
        
        new_message = {"role": "assistant", "content": ""}
        
        # Process AI's response for the current Bitcoin data
        for chunk_resp in completion:
            if chunk_resp.choices[0].delta.content:
                print(chunk_resp.choices[0].delta.content, end="", flush=True)
                new_message["content"] += chunk_resp.choices[0].delta.content
        
        # Add AI's response to the conversation history
        history.append(new_message)
        
        # Wait for 60 seconds before fetching data again
        time.sleep(60)
