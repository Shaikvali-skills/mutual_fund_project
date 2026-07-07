# 📊 Mutual Fund Data Analytics Capstone Project

## 📌 Project Overview

This project is a comprehensive Mutual Fund Data Analytics solution developed as part of the BlueStock Data Analytics Capstone. It focuses on collecting, cleaning, storing, analyzing, and visualizing mutual fund data to generate meaningful business insights.

The project follows the complete Data Analytics workflow:

- Data Collection
- Data Cleaning & ETL
- Database Design
- Exploratory Data Analysis (EDA)
- Financial Performance Analytics
- Advanced Analytics
- Interactive Dashboard
- Reporting

---

# 🎯 Objectives

- Build an automated ETL pipeline for mutual fund datasets.
- Store cleaned data in SQLite.
- Analyze fund performance using financial metrics.
- Visualize trends using Power BI.
- Recommend funds based on risk and performance.
- Generate insights for investors.

---

# 📂 Project Structure

```
MUTUAL_FUND_PROJECT/

├── data/
│   ├── raw/
│   ├── processed/
│   └── db/
│
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_Data Cleaning.ipynb
│   ├── 03_EDA_Analysis.ipynb
│   ├── 04_Performance Analytics.ipynb
│   └── 05_Advanced_Analytics.ipynb
│
├── scripts/
│   ├── etl_pipeline.py
│   ├── compute_metrics.py
│   ├── live_nav_fetch.py
│   └── recommender.py
│
├── sql/
│   ├── schema.sql
│   └── queries.sql
│
├── dashboard/
│   └── Mutual_Fund_Dashboard.pbix
│
├── reports/
│   ├── Final_Report.pdf
│   └── Presentation.pptx
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

# 📁 Dataset

The project uses Mutual Fund datasets containing:

- Fund Master
- NAV History
- AUM Details
- Scheme Performance
- Investor Transactions

Processed datasets are stored inside:

```
data/processed/
```

---

# 🛠 Technologies Used

- Python
- Pandas
- NumPy
- SQLite
- SQL
- Jupyter Notebook
- Power BI
- Matplotlib
- Seaborn
- Requests API
- Git & GitHub

---

# ⚙️ ETL Pipeline

The ETL pipeline performs the following tasks:

- Extract raw CSV files
- Remove duplicates
- Handle missing values
- Standardize column names
- Convert date columns
- Store cleaned data
- Load data into SQLite database

---

# 🗄 Database

SQLite is used as the backend database.

Database file:

```
data/db/bluestock_mf.db
```

Database tables include:

- fund_master
- nav_history
- fact_aum
- scheme_performance
- investor_transactions

---

# 📊 Exploratory Data Analysis

EDA includes:

- Missing Value Analysis
- Duplicate Analysis
- Distribution Analysis
- Correlation Analysis
- Fund Category Analysis
- AUM Analysis
- NAV Trends
- Performance Comparison

Visualizations include:

- Histograms
- Boxplots
- Bar Charts
- Line Charts
- Scatter Plots
- Heatmaps

---

# 📈 Performance Analytics

The following financial metrics were calculated:

- Daily Returns
- CAGR
- Volatility
- Sharpe Ratio
- Sortino Ratio
- Beta
- Alpha
- Tracking Error
- Maximum Drawdown
- Value at Risk (VaR)
- Conditional Value at Risk (CVaR)

---

# 🤖 Advanced Analytics

The project includes:

- Cohort Analysis
- Risk Analysis
- Fund Recommendation System
- VaR & CVaR Analysis

---

# 📊 Interactive Power BI Dashboard

The Power BI dashboard provides interactive insights into mutual fund performance, risk, and portfolio comparison. It consists of four pages with dynamic filters and slicers.

---

## 🏠 Dashboard 1: Industry Overview

This page provides an overall summary of the mutual fund dataset, including total funds, total AUM, average returns, and fund category distribution.

<p align="center">
<img width="1296" height="742" alt="Image" src="https://github.com/user-attachments/assets/8c4e7d48-9f4d-4a03-a50c-2f033bbd2fc5" />
</p>

---

## 📈 Dashboard 2: Performance Analysis

This page analyzes fund performance using CAGR, annual returns, Sharpe Ratio, and NAV trends.

<p align="center">
<img width="1291" height="727" alt="Image" src="https://github.com/user-attachments/assets/91fd9a91-61a1-4e0d-bf54-acad9545d8f0" />
</p>

---

## ⚠️ Dashboard 3: Risk Analysis

This page focuses on investment risk using Volatility, Maximum Drawdown, Beta, VaR, and CVaR.

<p align="center">
<img width="1291" height="725" alt="Image" src="https://github.com/user-attachments/assets/f06fa3f2-dcdd-42b1-954b-4976fefc45f1" />
</p>

---

## 🔄 Dashboard 4: Fund Comparison

This page enables users to compare multiple mutual funds based on returns, expense ratio, AUM, risk, and other key performance metrics.

<p align="center">
<img width="1283" height="722" alt="Image" src="https://github.com/user-attachments/assets/440d087c-8608-431d-b3b4-646db23d4fbc" />
</p>

Interactive slicers include:

- AMC
- Fund Category
- Date
- Risk Level

---

# 📋 SQL Queries

SQL scripts include:

- Table Creation
- Data Loading
- Fund Performance Queries
- Top Performing Funds
- Average Expense Ratio
- Highest AUM
- Risk Analysis Queries

---

# 📌 Key Insights

- Equity funds generated higher long-term returns than debt funds.
- Lower expense ratio funds generally delivered better risk-adjusted performance.
- Higher AUM does not always indicate superior returns.
- Sharpe Ratio effectively identifies consistent performers.
- Maximum Drawdown highlights downside risk across funds.

---

# 🚀 How to Run

### Clone Repository

```bash
git clone https://github.com/yourusername/mutual_fund_project.git
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run ETL Pipeline

```bash
python scripts/etl_pipeline.py
```

### Compute Performance Metrics

```bash
python scripts/compute_metrics.py
```

### Fetch Latest NAV

```bash
python scripts/live_nav_fetch.py
```

---

# 📷 Project Outputs

✔ Cleaned CSV Files

✔ SQLite Database

✔ SQL Queries

✔ EDA Notebooks

✔ Performance Analytics

✔ Advanced Analytics

✔ Power BI Dashboard

✔ Final Report

✔ Presentation

---

# 🔮 Future Improvements

- Live NAV updates using MFAPI
- Streamlit Web Application
- Portfolio Optimization using Markowitz Model
- Monte Carlo Simulation
- Automated Email Reporting

---

# 👨‍💻 Author

**Shaik Mohammad Vali**

Data Analyst | Python | SQL | Power BI | Excel

GitHub: https://github.com/Shaikvali-skills

LinkedIn: *(Add your LinkedIn profile URL here)*

---

# 📜 License

This project is developed for educational and learning purposes as part of the BlueStock Data Analytics Capstone Project.
