import pandas as pd

# Load datasets
funds = pd.read_csv("data/processed/01_fund_master.csv")
scorecard = pd.read_csv("data/processed/fund_scorecard.csv")

# Merge datasets
recommend_df = funds.merge(
    scorecard[['amfi_code', 'Sharpe_Ratio']],
    on='amfi_code',
    how='inner'
)

# Recommendation function
def recommend_funds(risk):
    result = (
        recommend_df[
            recommend_df['risk_category'].str.lower() == risk.lower()
        ]
        .sort_values('Sharpe_Ratio', ascending=False)
        [['scheme_name',
          'fund_house',
          'Sharpe_Ratio',
          'risk_category']]
        .head(3)
    )
    return result

# Main program
if __name__ == "__main__":

    print("=" * 60)
    print("        Mutual Fund Recommendation System")
    print("=" * 60)

    print("\nAvailable Risk Categories:")
    print(", ".join(sorted(recommend_df['risk_category'].unique())))

    risk = input("\nEnter Risk Category: ")

    recommendations = recommend_funds(risk)

    if recommendations.empty:
        print("\nNo funds found for this risk category.")
    else:
        print("\nTop 3 Recommended Funds:\n")
        print(recommendations.to_string(index=False))
        