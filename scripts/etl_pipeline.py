import os
import pandas as pd

RAW_PATH = "data/raw"
PROCESSED_PATH = "data/processed"

os.makedirs(PROCESSED_PATH, exist_ok=True)

files = [
    "fund_master.csv",
    "nav_history.csv",
    "investor_transactions.csv",
    "monthly_sip_inflows.csv",
    "portfolio_holdings.csv",
    "industry_folio.csv",
    "category_inflows.csv"
]

for file in files:
    file_path = os.path.join(RAW_PATH, file)

    if os.path.exists(file_path):
        print(f"Processing {file}...")

        df = pd.read_csv(file_path)

        # Remove duplicate rows
        df.drop_duplicates(inplace=True)

        # Remove rows where all values are missing
        df.dropna(how="all", inplace=True)

        # Remove extra spaces from column names
        df.columns = df.columns.str.strip()

        # Save cleaned file
        output_path = os.path.join(PROCESSED_PATH, file)
        df.to_csv(output_path, index=False)

        print(f"{file} cleaned successfully.")

    else:
        print(f"{file} not found.")

print("\nETL Pipeline Completed Successfully.")