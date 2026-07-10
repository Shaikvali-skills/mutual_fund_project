import pandas as pd

# Load cleaned NAV data
nav = pd.read_csv("data/processed/nav_history.csv")

# Convert date
nav["date"] = pd.to_datetime(nav["date"])

# Latest NAV for each fund
latest_nav = (
    nav.sort_values("date")
       .groupby("amfi_code")
       .last()
       .reset_index()
)

print("Latest NAV")
print(latest_nav.head())

# Daily Return
nav = nav.sort_values(["amfi_code", "date"])

nav["Daily Return (%)"] = (
    nav.groupby("amfi_code")["nav"]
       .pct_change() * 100
)

# Average Return
avg_return = (
    nav.groupby("amfi_code")["Daily Return (%)"]
       .mean()
       .reset_index()
)

print("\nAverage Daily Return")
print(avg_return.head())

# Save
avg_return.to_csv(
    "data/processed/fund_metrics.csv",
    index=False
)

print("\nMetrics generated successfully.")