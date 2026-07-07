# Data Dictionary: Bluestock Mutual Fund Database

## 1. Table: dim_fund (Dimension Table)
*Description: Contains descriptive attributes and master reference metadata for all mutual fund schemes.*

| Column Name | Data Type | Key | Business Definition | Source Reference / Lineage |
| :--- | :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PK | Association of Mutual Funds in India (AMFI) unique 6-digit identification code. | `01_fund_master.csv` |
| `fund_name` | TEXT | - | Official commercial name of the mutual fund scheme asset. | `01_fund_master.csv` |
| `category` | TEXT | - | Asset classification structure (e.g., Equity, Debt, Hybrid, Liquid). | `01_fund_master.csv` |
| `risk_level` | TEXT | - | Regulatory or asset risk profile tier assignment (e.g., Low, High, Very High). | `01_fund_master.csv` |

---

## 2. Table: dim_date (Dimension Table)
*Description: Time-dimension table supporting optimized chronological, historical, and fiscal trend groupings.*

| Column Name | Data Type | Key | Business Definition | Source Reference / Lineage |
| :--- | :--- | :--- | :--- | :--- |
| `date` | TEXT | PK | Full calendar date stored as an ISO 8601 string sequence (`YYYY-MM-DD`). | Derived Timeline |
| `year` | INTEGER | - | Calendar year numeral value integer (e.g., 2026). | Derived from `date` |
| `month` | INTEGER | - | Numeric month identifier index within the calendar year cycle (1 to 12). | Derived from `date` |
| `day` | INTEGER | - | Specific day day-of-month numeric index (1 to 31). | Derived from `date` |
| `quarter` | INTEGER | - | Fiscal reporting quarter partition block index (1 to 4). | Derived from `date` |

---

## 3. Table: fact_nav (Fact Table)
*Description: High-frequency transaction-log recording chronological net value pricing per fund unit.*

| Column Name | Data Type | Key | Business Definition | Source Reference / Lineage |
| :--- | :--- | :--- | :--- | :--- |
| `NAV_ID` | INTEGER | PK | Internal auto-incrementing surrogate index serial number. | SQLite Auto-Increment |
| `amfi_code` | INTEGER | FK | Associated operational target tracking asset fund key indicator. | `nav_history_cleaned.csv` |
| `date` | TEXT | FK | Settlement snapshot market evaluation execution timestamp pointer. | `nav_history_cleaned.csv` |
| `nav` | REAL | - | Continuous per-unit Net Asset Value net market valuation rate. | `nav_history_cleaned.csv` (F-filled) |

---

## 4. Table: fact_transactions (Fact Table)
*Description: Tracks individual transactional investment and redemption behavior records.*

| Column Name | Data Type | Key | Business Definition | Source Reference / Lineage |
| :--- | :--- | :--- | :--- | :--- |
| `transaction_id` | INTEGER | PK | Direct distinct ledger tracking item transaction serial index code. | `investor_transactions_cleaned.csv` |
| `investor_id` | INTEGER | - | Master account profile identification tracker key index code. | `investor_transactions_cleaned.csv` |
| `amfi_code` | INTEGER | FK | Mapped scheme indicator system index key reference pointer. | `investor_transactions_cleaned.csv` |
| `transaction_date`| TEXT | FK | Settled account booking execution timestamp value profile. | `investor_transactions_cleaned.csv` |
| `transaction_type`| TEXT | - | Standardized transaction categories (`SIP`, `Lumpsum`, `Redemption`). | `investor_transactions_cleaned.csv` |
| `amount` | REAL | - | Absolute transaction fiat value volume metric. | `investor_transactions_cleaned.csv` |
| `kyc_status` | TEXT | - | Standardized investor legal compliance framework status (`Yes`, `No`, `Pending`).| `investor_transactions_cleaned.csv` |
| `state` | TEXT | - | Regional compliance domicile location footprint. | `investor_transactions_cleaned.csv` |

---

## 5. Table: fact_performance (Fact)
*Description: Aggregates rolling analytical metrics assessing investment asset yields and expenses.*

| Column Name | Data Type | Key | Business Definition | Source Reference / Lineage |
| :--- | :--- | :--- | :--- | :--- |
| `performance_id` | INTEGER | PK | Internal performance assessment serialization counter tracking code. | SQLite Auto-Increment |
| `amfi_code` | INTEGER | FK | Target validation lookup code tracking across assets. | `scheme_performance_cleaned.csv` |
| `return_1y` | REAL | - | Trailing 1-Year annualized percentage yield metric factor. | `scheme_performance_cleaned.csv` |
| `return_3y` | REAL | - | Trailing 3-Year compound annual rate of return metric factor. | `scheme_performance_cleaned.csv` |
| `return_5y` | REAL | - | Trailing 5-Year compound annual rate of return metric factor. | `scheme_performance_cleaned.csv` |
| `expense_ratio` | REAL | - | Asset total operational management deduction charge percentage fee. | `scheme_performance_cleaned.csv` |
| `anomaly_flag` | INTEGER | - | Integrity validation binary threshold signal (`1` = flagged outlier).| Computed via Pipeline |

---

## 6. Table: fact_aum (Fact Table)
*Description: Logs net periodic values summarizing aggregate assets under management metrics.*

| Column Name | Data Type | Key | Business Definition | Source Reference / Lineage |
| :--- | :--- | :--- | :--- | :--- |
| `aum_id` | INTEGER | PK | Unique record line primary sequence serial verification number. | SQLite Auto-Increment |
| `amfi_code` | INTEGER | FK | Fund identification key matching back to master dimension table. | `aum_cleaned.csv` |
| `date` | TEXT | FK | Inventory evaluation tracking timestamp reference key code. | `aum_cleaned.csv` |
| `total_aum` | REAL | - | Metric sum representing absolute total Assets Under Management. | `aum_cleaned.csv` |