Data Quality Summary — Day 1 Ingestion
I’ve completed the initial exploration and cross-validation of our raw datasets for the Mutual Fund Analytics project. Here is the breakdown of what was checked, the results, and the key anomalies to keep an eye on.

1. Dataset Profiles
01_fund_master.csv: Contains exactly 40 fund schemes with 15 columns of descriptive data (fund house, category, sub-category, etc.). The file is completely clean—no missing fields or empty rows detected.

02_nav_history.csv: A much larger transactional history file containing over 46,000 historical daily NAV records tracking back to our fund master codes.

2. Referential Integrity Check (AMFI Codes)
Status: PASS

Finding: I ran a full cross-reference check to confirm if every amfi_code listed in our Master file actually has historical pricing data inside the transaction history logs. 100% of the codes matched up perfectly. There are no orphaned fund codes or missing historical data pieces.

3. Key Data Anomalies & Mitigation
Scheme Name Mismatch Across Files: When looking closely at the data, the scheme names inside the individual NAV files do not match the clean scheme names in our master list. For example, code 119551 is labeled "SBI Bluechip Fund" in the master sheet but shows up as "Aditya Birla Sun Life Banking & PSU Debt Fund" in the raw daily records. Similarly, the remaining NAV files maps back to an entirely different name structure.

Mitigation: Never map or join tables using the scheme name text. Because text names are fluctuating wildly across different API source files, all data relationships and table merges must strictly use the unique numeric amfi_code (or scheme_code). For our final dashboards and reports, we will strictly display the clean names pulled from 01_fund_master.csv so the layout stays professional and consistent.