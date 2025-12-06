# U.S. Natural Gas Demand Forecasting  
### End-to-End Data Pipeline • ML Forecasting • DuckDB • Streamlit Dashboard

This project builds a **fully reproducible, end-to-end forecasting system** for U.S. natural gas demand using:

- **EIA monthly natural gas consumption data (2001–2025)**
- **Custom feature engineering** for time-series modeling
- **XGBoost and LightGBM** regression models
- A **recursive 12-month forecast** for the state of Texas
- A **DuckDB OLAP database** for fast analytics
- An interactive **Streamlit dashboard** for exploration of all 50 states

The goal is to demonstrate a *production-style* data science workflow:  
**ETL → Feature Engineering → ML Modeling → Forecasting → Database → Dashboard**.

---

# 📁 Project Structure

natural_gas_forecasting/
│
├── data/
│ ├── raw/ # Original downloaded EIA CSV
│ ├── processed/ # Cleaned data + model FE datasets
│ │ ├── consumer_gas_monthly_cleaned.csv
│ │ └── model_data_texas.csv
│ │ └── texas_forecast_12m.csv
│ └── external/ # (future) weather, prices, etc.
│
├── models/
│ ├── xgb_texas_model.json # Saved best model (XGBoost)
│ └── (future) lgbm model
│
├── notebooks/
│ ├── data_cleaning.ipynb # Cleaning & preprocessing
│ ├── duckdb_creation.ipynb # Create gas_wide & gas_long tables
│ ├── feature_engineering.ipynb # FE for Texas (lags, rolling, etc.)
│ ├── texas_model.ipynb # Train/evaluate baseline, LGBM, XGB
│ └── forecast_texas.ipynb # Recursive 12-month forecast
│
├── streamlit_app/
│ └── app.py # Interactive dashboard
│
├── natural_gas.duckdb # DuckDB OLAP database
├── requirements.txt
└── README.md


---

# 🗂️ Data Source

**EIA: Natural Gas Delivered to Consumers (Monthly, MMcf)**  
Includes:

- U.S. Total  
- All 50 states + DC  
- Monthly data from **2001 → 2025**

The dataset captures **consumer demand** (residential, commercial, industrial, electric power).

---

# 🧹 Data Cleaning

The raw CSV contained metadata rows and verbose column names.  
Cleaning steps included:

- Removing EIA metadata rows
- Converting `"Jan-2001"` → proper `datetime` index
- Renaming long state columns to simple names (`Alabama`, `Texas`, `US_Total`, ...)
- Ensuring all values are numeric
- Saving a clean, wide-format time series

Resulting cleaned dataset:

Date (index), US_Total, Alabama, Alaska, ..., Texas, ..., Wyoming


---

# 🗄️ DuckDB: Analytical Data Backend

A DuckDB database (`natural_gas.duckdb`) stores:

### **1. gas_wide**  
Wide time series:  
Date | Alabama | Alaska | ... | Texas | ...


### **2. gas_long**  
Unpivoted table (used by Streamlit):  
Date | state | value


### **3. gas_forecast**  
Texas 12-month forecast added via CSV import:  
Date | state | value | source | horizon


DuckDB enables **fast SQL queries**, lightweight storage, and frictionless integration with Streamlit.

---

# 🧠 Feature Engineering (Texas Model)

For Texas, we engineered a comprehensive time-series feature set:

### 📌 Lag features  
`lag_1`, `lag_2`, `lag_3`, `lag_6`, `lag_12`, `lag_24`

### 📌 Rolling windows  
`rolling_3`, `rolling_6`, `rolling_12`, `rolling_12_std`, `rolling_24`, `rolling_36`

### 📌 Calendar / seasonality  
`month`, `quarter`, `year`,  
`is_winter`, `is_summer`,  
cyclical encodings: `month_sin`, `month_cos`

### 📌 YoY differences  
`yoy_change`, `yoy_24`

These features provide memory, smooth trends, seasonal structure, and nonlinear relationships that ML models can exploit.

The FE dataset is saved as:

data/processed/model_data_texas.csv


---

# 🤖 Modeling

Three models were trained and evaluated:

- **Baseline model** (simple lag-based)
- **LightGBM regressor**
- **XGBoost regressor** ← **Best model**

### 🔬 Evaluation Window  
Model performance was measured on a realistic holdout set (last ~2 years of data).

---

# 📊 Model Performance

XGBoost outperformed all other models across every metric:

| Model       | RMSE          | MAE           | MAPE      | MedAE        | R²        |
| ----------- | ------------- | ------------- | --------- | ------------ | --------- |
| Baseline    | 49,771.97     | 41,969.50     | 11.07%    | 37,010.50    | -0.435    |
| LightGBM    | 25,489.12     | 16,314.11     | 3.98%     | 8,596.74     | 0.624     |
| **XGBoost** | **19,074.52** | **12,529.61** | **3.06%** | **6,991.25** | **0.789** |

### 🧭 Interpretation

XGBoost captures:

- nonlinear interactions across time
- long-horizon seasonal patterns via 12–24 month lags
- volatility via rolling windows
- cyclical seasonality through sine/cosine encodings

The baseline model fails to capture seasonal or structural dynamics.  
LightGBM underfits slightly due to different tree structure + constraints.

---

# 🔮 12-Month Forecast (Texas)

Using the trained XGBoost model:

- A **recursive forecasting pipeline** predicts 12 months beyond the final available date (June 2025)
- Forecasts are saved to:  
  `data/processed/texas_forecast_12m.csv`
- Forecasts are written into DuckDB (`gas_forecast` table)
- Streamlit shows a **historical + forecast** panel with a dashed vertical line marking forecast start

The Texas forecast is included in the dashboard as a dedicated visualization section.

---

# 📊 Streamlit Dashboard

Run the dashboard:

```bash
streamlit run streamlit_app/app.py


Dashboard Features

📈 Interactive line charts for any state or group of states

🗺️ U.S. choropleth map (monthly or annual aggregation)

📊 Summary statistics for any selected range

🔮 Texas Historical + 12-Month Forecast panel

⏳ Sidebar controls for:

State selection

Date range

Monthly vs annual aggregation

Built on DuckDB, queries are extremely fast even on large datasets.

Installation

```bash
pip install -r requirements.txt
```

To run the Streamlit app:

```bash`
streamlit run streamlit_app/app.py
```

Future Improvements

Add multi-state forecasting (CA, NY, FL, etc.)

Incorporate exogenous variables:

weather (HDD/CDD)

natural gas spot prices

economic indicators

Hyperparameter tuning / cross-validation

Deploy Streamlit app online

Add automated daily/weekly pipelines using scripts instead of notebooks

References

U.S. Energy Information Administration (EIA) – Natural Gas Delivered to Consumers

XGBoost documentation

LightGBM documentation

DuckDB project

Streamlit documentation

Summary

This project demonstrates a full-stack data science workflow:

Clean real-world energy data

Engineer predictive features

Train & evaluate ML models

Generate forward forecasts

Store data in a modern analytical database

Visualize insights through an interactive dashboard

It is designed as a portfolio-quality example of practical, production-oriented forecasting.

