import requests
import json
import pandas as pd

# Replace these with your list of user addresses
USER_ADDRESSES = [
    '0xddapfaad4b3b3b3b3b3b3b3b3b3b3b3b3b3b3b3',
    # Add more addresses here
]

# Base URL for Hyperliquid API
BASE_URL = 'https://api.hyperliquid.xyz/info'

# Headers for the request
headers = {
    'Content-Type': 'application/json'
}

# Function to fetch balances
def fetch_balances(user_address):
    data = {
        "type": "spotClearinghouseState",
        "user": user_address
    }
    try:
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching balances for {user_address}: {e}")
        return None

# Function to fetch token prices
def fetch_token_prices():
    data = {
        "type": "spotMetaAndAssetCtxs"
    }
    try:
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching token prices: {e}")
        return None

# Fetch token prices once since they are the same for all users
prices_response = fetch_token_prices()

if prices_response:
    tokens = prices_response[0]['tokens']
    universe = prices_response[0]['universe']
    prices = prices_response[1]

    # Create a mapping from token index to token name
    token_index_to_name = {index: token['name'] for index, token in enumerate(tokens)}

    # Create a mapping from token name to its mid price
    token_prices = {}
    for idx, pair in enumerate(universe):
        token_indices = pair['tokens']
        token_names = [token_index_to_name[index] for index in token_indices if token_index_to_name[index] != 'USDC']
        mid_price = prices[idx]['midPx']
        if token_names:
            token_prices[token_names[0]] = float(mid_price)

    # Main DataFrame to store all addresses' data
    all_addresses_data = []

    for address in USER_ADDRESSES:
        balances_response = fetch_balances(address)
        
        if balances_response:
            balances = balances_response.get('balances', [])
            balance_data = []

            for asset in balances:
                coin = asset['coin']
                total = float(asset['total'])
                hold = float(asset['hold'])
                price = token_prices.get(coin, 1.0)  # Default price is 1.0 for USDC or if not found
                usd_value = total * price
                balance_data.append({
                    'Coin': coin,
                    'Total': round(total, 4),
                    'Hold': round(hold, 4),
                    'Price (USD)': price,
                    'Value (USD)': round(usd_value, 2)
                })

            df = pd.DataFrame(balance_data)
            df.loc['Total'] = df[['Value (USD)']].sum()
            all_addresses_data.append({'Address': address, 'Data': df})
        else:
            print(f"Failed to fetch balances for address {address}")

    # Convert list of dicts to DataFrame
    result_df = pd.DataFrame(all_addresses_data)

    # Display each DataFrame for each address
    for entry in all_addresses_data:
        address = entry['Address']
        df = entry['Data']
        print(f"\nAddress: {address}")
        print(df)

    # Sum up all account values
    total_value_usd = sum(df.loc['Total', 'Value (USD)'] for df in result_df['Data'])
    print(f"\nTotal Value (USD) across all addresses: {round(total_value_usd, 2)}")

else:
    print("Failed to fetch prices.")
