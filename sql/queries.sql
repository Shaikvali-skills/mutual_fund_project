-- Active: 1782311876147@@127.0.0.1@3306

#top 5 funds by AUM
SELECT fund_house, Sum(aum_crore) as total_aum
FROM fact_aum
group by fund_house
order by total_aum desc
limit 5;


#-- 2. Average NAV Per Month for Each Fund Scheme
select amfi_code, strftime('%Y-%m',date) as Month, Avg(nav) as Avg_NAV
from fact_nav
group by amfi_code, Month
order by amfi_code, Month;

#3 --write a SQL query for SIP YoY growth
select amfi_code, strftime('%Y',transaction_date) as Year, sum(amount_inr) as Total_SIP_Amount
from fact_transactions
where transaction_type = 'SIP' 
group by amfi_code, Year
order by amfi_code, Year;

#4. Transactions by State
select state, count(*) as Total_Transactions
from fact_transactions
group by state
order by Total_Transactions desc;

#5. Funds with Expense Ratio < 1%

select fund_house, amfi_code, expense_ratio_pct
from fact_performance
where expense_ratio_pct < 1.0
group by fund_house, amfi_code, expense_ratio_pct
order by expense_ratio_pct asc;


#6. Popularity of Transaction Types (Choice #1)

select Transaction_type, count(*) as Total_Transactions
from fact_transactions
group by Transaction_type
order by Total_Transactions desc;   

#7. Investor Lifetime Value (Ranked)
select investor_id, sum(amount_inr) as Lifetime_Value, dense_rank() over (order by sum(amount_inr) DESC) as Rank
from fact_transactions
Group by investor_id;


#8. Total Investment Volumes by Payment Mode
SELECT 
    t.payment_mode,
    COUNT(*) AS total_transactions,
    SUM(t.amount_inr) AS total_volume_inr
FROM fact_transactions t
GROUP BY t.payment_mode
ORDER BY total_volume_inr DESC;

#9 Total number of transaction by each payment_mode
select payment_mode, count(*) as total_payment_modes
from fact_transactions
GROUP BY payment_mode
ORDER BY total_payment_modes desc;


#10 Top 1 investors by state

SELECT investor_id, state, Total_lifetime_investment, Ranking
FROM (
    SELECT investor_id, state, sum(amount_inr) as Total_lifetime_investment, 
    dense_rank() OVER(PARTITION BY state ORDER BY sum(amount_inr) DESC) as Ranking
    FROM fact_transactions
    GROUP BY investor_id, state
) as subquery
WHERE Ranking = 1
ORDER BY Total_lifetime_investment DESC;


WITH state_rankings AS (
    SELECT 
        investor_id, 
        state,
        SUM(amount_inr) AS Total_lifetime_investment, 
        DENSE_RANK() OVER(PARTITION BY state ORDER BY SUM(amount_inr) DESC) AS rank
    FROM fact_transactions
    GROUP BY investor_id, state
)
SELECT investor_id, Total_lifetime_investment, state
FROM state_rankings
WHERE rank = 1
ORDER BY Total_lifetime_investment DESC;




select nav, count(*) as Total from fact_nav;

