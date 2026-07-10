import pandas as pd

nav = pd.read_csv("data/processed/nav_history.csv")

nav["date"] = pd.to_datetime(nav["date"])

latest = (
    nav.sort_values("date")
       .groupby("amfi_code")
       .last()
       .reset_index()
)

print("Latest NAV Data")
print(latest[["amfi_code", "date", "nav"]].head(10))
