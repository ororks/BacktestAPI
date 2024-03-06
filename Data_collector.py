import pandas as pd
import requests
from datetime import datetime, timezone

def collect_APIdata(symbols: list[str], dates:list[str], interval:str):
    url = "https://data-api.binance.vision/api/v3/klines"
    start_date = datetime.strptime(dates[0], '%Y-%m-%d').replace(tzinfo=timezone.utc)
    start_date = int(start_date.timestamp() * 1000)
    end_date = datetime.strptime(dates[1], '%Y-%m-%d').replace(tzinfo=timezone.utc)
    end_date = int(end_date.timestamp() * 1000)
    user_data = None
    df_dico = {}
    for symbol in symbols:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_date,
            'endTime': end_date
        }
        response = requests.get(url, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time',
                                         'Quote_volume', 'Nb_trades', 'ignore1', 'ignore2', 'ignore3'])
        df['Dates'] = pd.to_datetime(df['Open_time'], unit='ms')
        df = df[['Close']].set_index(df['Dates'])
        #df.columns = [f'{symbol}_{var}' for var in df.columns]
        df_dico[symbol] = df
        # if user_data is None:
        #     user_data = df
        # else:
        #     user_data = user_data.join(df, how='outer')
    #user_data_dict = user_data.to_dict(orient="index")
    #user_data.index.strftime('%Y-%m-%d')
    return df_dico

if __name__ == '__main__':
    user_data = collect_APIdata(['ETHBTC', 'BNBETH'], ['2023-01-01', '2023-01-02'], '1d')
    print(user_data)