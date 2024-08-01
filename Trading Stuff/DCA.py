import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import glob

def load_data(files):
    dataframes = {}
    for file in files:
        df = pd.read_csv(file)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        dataframes[file] = df
    return dataframes

def simulate_dca_strategy(data, dca_amount, frequency='daily'):
    if frequency == 'hourly':
        period = 'H'
    elif frequency == 'daily':
        period = 'D'
    elif frequency == 'weekly':
        period = 'W'
    elif frequency == 'monthly':
        period = 'MS'  # Month start
    else:
        raise ValueError("Frequency must be one of: hourly, daily, weekly, monthly")

    # Resample data based on frequency
    resampled_data = data.resample(period).last().dropna()

    # Calculate number of purchases
    num_purchases = len(resampled_data)

    # Calculate total investment and total asset purchased
    total_investment = num_purchases * dca_amount
    total_asset_purchased = total_investment / resampled_data['Close'].mean()

    # Calculate final portfolio value
    final_portfolio_value = total_asset_purchased * resampled_data['Close'].iloc[-1]

    # Calculate average price paid
    average_price_paid = total_investment / total_asset_purchased

    # Create a DataFrame to store purchase points
    purchases = resampled_data.copy()
    purchases['DCA'] = dca_amount  # Use dca_amount instead of 0

    return final_portfolio_value, total_investment, purchases, average_price_paid

# Load all CSV files in the current directory
csv_files = glob.glob("*.csv")

# Define the total investment capital
total_investment_capital = float(input("Enter the total investment capital: "))
frequency = input("Enter the frequency (hourly, daily, weekly, monthly): ").lower()

# Load data from all CSV files
dataframes = load_data(csv_files)

# Divide the total capital evenly across all assets
dca_amount_per_asset = total_investment_capital / len(csv_files)

# Track the best results
best_value = 0
best_amount = 0
best_frequency = ''
best_roi = 0
results = {}

# Variables to track overall performance
total_final_value = 0
total_total_investment = 0

# Run simulations for each asset
for file, df in dataframes.items():
    final_value, total_investment, purchases, average_price_paid = simulate_dca_strategy(df, dca_amount_per_asset, frequency)
    roi = ((final_value - total_investment) / total_investment) * 100
    results[file] = {
        'Final Value': final_value,
        'Total Investment': total_investment,
        'ROI': roi,
        'Purchases': purchases,
        'Average Price Paid': average_price_paid
    }
    print(f"\nAsset: {file}")
    print(f"Final Value = ${final_value:.2f}")
    print(f"Total Investment = ${total_investment:.2f}")
    print(f"ROI = {roi:.2f}%")
    print(f"Average Price Paid = ${average_price_paid:.2f}")

    # Update overall totals
    total_final_value += final_value
    total_total_investment += total_investment

    if final_value > best_value:
        best_value = final_value
        best_amount = dca_amount_per_asset
        best_frequency = frequency
        best_roi = roi

# Calculate overall ROI
overall_roi = ((total_final_value - total_total_investment) / total_total_investment) * 100

# Output the best result
print("\nBest DCA Strategy:")
print(f"Amount Invested per Asset: ${best_amount}")
print(f"Frequency: {best_frequency}")
print(f"Final Portfolio Value: ${best_value:.2f}")
print(f"ROI: {best_roi:.2f}%")
print(f"\nOverall ROI for all investments: {overall_roi:.2f}%")
print(f"Total Amount Invested: ${total_total_investment:.2f}")
print(f"Total Return: ${total_final_value - total_total_investment:.2f} (${total_final_value:.2f})")

# Plot the normalized price for each asset on a single chart
plt.figure(figsize=(14, 7))
for file, result in results.items():
    normalized_prices = (result['Purchases']['Close'] / result['Purchases']['Close'].iloc[0] - 1) * 100
    plt.plot(normalized_prices.index, normalized_prices, label=f"{file}: Final Value = ${result['Final Value']:.2f}, ROI = {result['ROI']:.2f}%, Avg Price Paid = ${result['Average Price Paid']:.2f}".replace('$', r'\$'))

plt.title('Normalized Price Over Time for Multiple Assets')
plt.xlabel('Date')
plt.ylabel('Percentage Change from Initial Value (%)')
plt.legend()
plt.show()
