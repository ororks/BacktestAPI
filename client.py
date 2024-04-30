import requests

url = "https://backtestapi.onrender.com/backtesting/"
fonction_trading = """
import pandas as pd
import scipy
def func_strat(dfs_dict):
    df_returns = pd.DataFrame()
    for key, df in dfs_dict.items():
        df_returns[key] = df["Close"]
    df_returns = df_returns.pct_change().fillna(0)
    nb_actifs = len(df_returns.columns)
    pond = {col: 1.0 / nb_actifs for col in df_returns.columns}
    poids_ts = pd.DataFrame(index=df_returns.index, columns=df_returns.columns)

    changement_pond = 0.1

    for i, date in enumerate(df_returns.index):

        if i % 2 == 0 and i > 0:
            total_pond = 0
            for col in df_returns.columns:
                rendement_2_jours = df_returns[col].iloc[i] - df_returns[col].iloc[i - 2]
                if rendement_2_jours > 0:
                    pond[col] = min(pond[col] + changement_pond, 1)
                else:
                    pond[col] = max(pond[col] - changement_pond, 0)
                total_pond += pond[col]

            for col in pond:
                pond[col] /= total_pond

        for col in df_returns.columns:
            poids_ts.at[date, col] = pond[col]

    return poids_ts
"""

params = {
    "func_strat": fonction_trading,
    "requirements": ["pandas", "scipy"],
    "tickers": ["ETHBTC", "BNBETH"],
    "dates": ["2022-01-01", "2023-01-07"],
    "interval": "1d",
    "amount": "10000",
    "request_id": "random_request_2",
    "is_recurring": True,
    "repeat_frequency": 1,
    "nb_execution": 4,
}

response = requests.post(url, json=params)
response = response.json()
print("Data received from response:", response)

################################################ /get_result ##########################################################

url = "https://backtestapi.onrender.com/get_result"
params = {
    "request_id": "random_request_1"
}
response = requests.get(url, params=params)
print(response.json())
