"""
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Author: Jose Diaz Ayala - Neuralbytes
"""


import numpy as np
import pandas as pd
import json
import os
import pickle
import matplotlib.pyplot as plt
import argparse
import sys
import random

# Step 1: Set up the argument parser
parser = argparse.ArgumentParser(description="Run stock trading simulations based on user-defined parameters.")
parser.add_argument('--num', type=int, default=5, help='Number of simulations to run')
parser.add_argument('--file', type=str, required=True, help='Path to the CSV file containing stock data')
parser.add_argument('--limit_trades', type=bool, default=False, help='Limit the maximum number of trades per simulation')

# Step 2: Parse arguments
args = parser.parse_args()

# Validate and handle the arguments
try:
    # Check if the number of simulations is a positive integer
    if args.num <= 0:
        raise ValueError("Number of simulations must be a positive integer.")

    # Attempt to open the specified file to ensure it exists
    with open(args.file, 'r') as file:
        pass  # If the file opens successfully, we do nothing else here

except FileNotFoundError:
    print(f"Error: The file '{args.file}' does not exist. Please check the file path and try again.")
    sys.exit(1)  # Exit the script with an error code
except ValueError as e:
    print(f"Error: {e}")
    sys.exit(1)  # Exit the script with an error code
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)  # Exit the script with an error code

# Parameters
window = 20
num_std_dev = 2
initial_cash = 1000  # Total amount of money to start with
max_single_order_amount = 100  # Max amount for a single order
cooldown_period_base = 45  # Base cooldown period in steps
stop_loss_percentage = 0.05  # Stop-loss at 5% below purchase price
num_actions = 3  # Number of actions: Buy, Sell, Hold
maker_fee_percentage = 0.0038  # Maker fee per transaction
taker_fee_percentage = 0.0057  # Taker fee per transaction

# Q-learning parameters
epsilon_base = 0.2  # Base exploration rate
alpha_base = 0.1  # Base learning rate
gamma_base = 0.9  # Base discount factor

# Step 3: Assign arguments to variables
num_simulations = args.num  # Number of simulations to run
limit_trades = args.limit_trades  # Limit the maximum number of trades per simulation

# Model
output_file = 'simulation_results.json'
q_table_file = 'q_table.pkl'

# Load historical stock data from CSV file
csv_file_path = args.file  # Ensure the CSV file is in the current working directory
historical_data = pd.read_csv(csv_file_path, parse_dates=['Date'])
historical_data.set_index('Date', inplace=True)

# Load or initialize Q-table
if os.path.exists(q_table_file):
    with open(q_table_file, 'rb') as f:
        q_table = pickle.load(f)
else:
    q_table = np.zeros((window, num_actions))  # Initialize Q-table

# Calculate Moving Average and Bollinger Bands
def calculate_moving_average(data, window):
    return data.rolling(window=window).mean()

def calculate_bollinger_bands(data, window, num_std_dev):
    rolling_mean = calculate_moving_average(data, window)
    rolling_std = data.rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * num_std_dev)
    lower_band = rolling_mean - (rolling_std * num_std_dev)
    return rolling_mean, upper_band, lower_band

# Perform action and update portfolio
def perform_action(action, price, portfolio, transaction_log, max_trades, cooldown_counter, epsilon, alpha, gamma):
    reward = 0
    fees = 0

    if cooldown_counter > 0:
        cooldown_counter -= 1
        return reward, fees, cooldown_counter  # During cooldown period, no action is taken

    fee_percentage = maker_fee_percentage if action == 0 else taker_fee_percentage

    if action == 0:  # Buy
        if portfolio['cash'] > 0 and (not limit_trades or len(portfolio['investments']) < max_trades):
            amount_to_invest = min(portfolio['cash'], max_single_order_amount)
            amount = amount_to_invest / price
            cost = amount * price * (1 + fee_percentage)
            portfolio['cash'] -= cost
            fees += amount * price * fee_percentage
            stop_loss_price = price * (1 - stop_loss_percentage)
            portfolio['investments'].append((price, amount, stop_loss_price))
            transaction_log.append({'type': 'buy', 'amount': amount, 'price': price, 'total_spent': cost, 'reason': 'buy_signal'})
    elif action == 1:  # Sell
        if len(portfolio['investments']) > 0:
            sell_amount = 0
            for i, (buy_price, invest_amount, stop_loss_price) in enumerate(portfolio['investments']):
                if invest_amount > 0:
                    amount_to_sell = min(invest_amount, max_single_order_amount / price)
                    revenue = amount_to_sell * price * (1 - fee_percentage)
                    portfolio['cash'] += revenue
                    fees += amount_to_sell * price * fee_percentage
                    portfolio['investments'][i] = (buy_price, invest_amount - amount_to_sell, stop_loss_price)
                    sell_amount += amount_to_sell
                    transaction_log.append({'type': 'sell', 'amount': amount_to_sell, 'price': price, 'total_gained': revenue, 'reason': 'sell_signal'})
                    if sell_amount >= max_single_order_amount / price:
                        break
    elif action == 2:  # Hold
        transaction_log.append({'type': 'hold', 'reason': 'hold_signal'})

    # Apply stop-loss for each position
    for i, (buy_price, invest_amount, stop_loss_price) in enumerate(portfolio['investments']):
        if price <= stop_loss_price and invest_amount > 0:
            amount_to_sell = min(invest_amount, max_single_order_amount / price)
            revenue = amount_to_sell * price * (1 - fee_percentage)
            portfolio['cash'] += revenue
            fees += amount_to_sell * price * fee_percentage
            portfolio['investments'][i] = (buy_price, invest_amount - amount_to_sell, stop_loss_price)
            transaction_log.append({'type': 'sell (stop-loss)', 'amount': amount_to_sell, 'price': price, 'total_gained': revenue, 'reason': 'stop_loss'})
            if invest_amount - amount_to_sell <= 0:
                portfolio['investments'].pop(i)

    # Reward calculation
    reward = get_total_portfolio_value(price, portfolio) - initial_cash

    return reward, fees, cooldown_counter

def get_total_portfolio_value(price, portfolio):
    investment_value = sum(amount * price for _, amount, _ in portfolio['investments'])
    return portfolio['cash'] + investment_value

def get_number_of_shares(portfolio):
    return sum(amount for _, amount, _ in portfolio['investments'])

def get_average_cost_per_share(portfolio):
    total_cost = sum(buy_price * amount for buy_price, amount, _ in portfolio['investments'])
    total_amount = get_number_of_shares(portfolio)
    return total_cost / total_amount if total_amount > 0 else 0

def choose_action(state, q_table, epsilon):
    if np.random.rand() < epsilon:  # Exploration
        return np.random.choice(num_actions)
    else:  # Exploitation
        return np.argmax(q_table[state])

def update_q_table(state, action, reward, next_state, q_table, alpha, gamma):
    best_next_action = np.argmax(q_table[next_state])
    td_target = reward + gamma * q_table[next_state, best_next_action]
    td_error = td_target - q_table[state, action]
    q_table[state, action] += alpha * td_error

def reset_portfolio():
    return {
        'cash': initial_cash,
        'investments': [],
        'transactions': [],
        'total_fees': 0
    }

def adjust_parameters(reward, epsilon, alpha, gamma, cooldown_period):
    if reward > 0:
        epsilon *= 0.99  # Decrease exploration if reward is positive
        alpha *= 1.01  # Increase learning rate
        gamma *= 1.01  # Increase discount factor
        cooldown_period = max(1, cooldown_period - 1)  # Decrease cooldown period
    else:
        epsilon *= 1.01  # Increase exploration if reward is negative
        alpha *= 0.99  # Decrease learning rate
        gamma *= 0.99  # Decrease discount factor
        cooldown_period += 1  # Increase cooldown period

    return epsilon, alpha, gamma, cooldown_period

# Run backtest
def run_backtest(max_trades):
    global current_step, q_table
    portfolio = reset_portfolio()
    transaction_log = []
    historical_data['MA'] = np.nan
    historical_data['Upper Band'] = np.nan
    historical_data['Lower Band'] = np.nan

    # Initialize dynamic parameters
    epsilon = epsilon_base
    alpha = alpha_base
    gamma = gamma_base
    cooldown_period = cooldown_period_base
    cooldown_counter = 0

    for date, row in historical_data.iterrows():
        price = row['Adj Close']
        stock_data = historical_data.loc[:date, 'Adj Close']
        if len(stock_data) >= window:
            rolling_mean, upper_band, lower_band = calculate_bollinger_bands(stock_data, window, num_std_dev)
            historical_data.at[date, 'MA'] = rolling_mean.iloc[-1]
            historical_data.at[date, 'Upper Band'] = upper_band.iloc[-1]
            historical_data.at[date, 'Lower Band'] = lower_band.iloc[-1]

        state = current_step % window
        action = choose_action(state, q_table, epsilon)
        reward, fees, cooldown_counter = perform_action(action, price, portfolio, transaction_log, max_trades, cooldown_counter, epsilon, alpha, gamma)
        next_state = (current_step + 1) % window
        update_q_table(state, action, reward, next_state, q_table, alpha, gamma)

        portfolio['total_fees'] += fees

        if get_total_portfolio_value(price, portfolio) <= 0:
            q_table = np.zeros((window, num_actions))  # Reset Q-table
            portfolio = reset_portfolio()
            cooldown_counter = cooldown_period_base
            print(f"Total portfolio value depleted on {date}. Resetting portfolio and saving Q-table.")

        epsilon, alpha, gamma, cooldown_period = adjust_parameters(reward, epsilon, alpha, gamma, cooldown_period)

        current_step += 1

    final_price = historical_data['Adj Close'].iloc[-1]
    final_portfolio_value = get_total_portfolio_value(final_price, portfolio)
    shares_held = get_number_of_shares(portfolio)
    average_cost_per_share = get_average_cost_per_share(portfolio)

    result = {
        'final_portfolio_value': final_portfolio_value,
        'shares_held': shares_held,
        'average_cost_per_share': average_cost_per_share,
        'transactions': transaction_log,
        'total_fees': portfolio['total_fees']
    }

    return result

# Run multiple simulations and store results
simulation_results = []
portfolio_values = []

for i in range(num_simulations):
    current_step = 0
    max_trades = random.randint(1, 5) if limit_trades else float('inf')  # Randomly select the maximum number of trades if limit_trades is True
    print(f"Running simulation {i+1}/{num_simulations} with a max of {max_trades} trades" if limit_trades else f"Running simulation {i+1}/{num_simulations} with no trade limit")
    result = run_backtest(max_trades)
    simulation_results.append(result)
    portfolio_values.append(result['final_portfolio_value'])

    # Save Q-table after each simulation
    with open(q_table_file, 'wb') as f:
        pickle.dump(q_table, f)

# Save results to JSON file
with open(output_file, 'w') as f:
    json.dump(simulation_results, f, indent=4)

# Display summary of each simulation
for i, result in enumerate(simulation_results):
    print(f"Simulation {i+1} Summary:")
    print(f"Final Portfolio Value: ${result['final_portfolio_value']:.2f}")
    print(f"Shares Held: {result['shares_held']:.4f}")
    print(f"Average Cost Per Share: ${result['average_cost_per_share']:.2f}")
    print(f"Total Fees: ${result['total_fees']:.2f}")
    print("\n")

# Plotting the final portfolio values of each simulation
plt.figure(figsize=(10, 6))
plt.plot(range(1, num_simulations + 1), portfolio_values, marker='o', linestyle='-', color='b')
plt.title('Final Portfolio Values Over Multiple Simulations')
plt.xlabel('Simulation Number')
plt.ylabel('Final Portfolio Value')
plt.grid(True)
plt.show()

