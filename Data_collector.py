import pandas as pd
import requests


class DataCollector:
    def __init__(self, tickers: list[str], start_date: str, end_date: str, interval: str):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.data = {}

    def collect_data(self, ticker):
        api_url = 'https://api.binance.com/api/v3/klines'
        start_time = pd.Timestamp(self.start_date)
        end_time = pd.Timestamp(self.end_date)
        start = int(start_time.timestamp() * 1000)
        end = int(end_time.timestamp() * 1000)
        all_data = []
        params = {
            'symbol': ticker,
            'interval': self.interval,
            'limit': 1000
        }
        while start < end:
            params['startTime'] = start
            response = requests.get(api_url, params=params)
            if response.status_code == 200:
                data = response.json()
                all_data.extend(data)
                start = int(data[-1][0]) + 1
            else:
                print("Erreur lors de la récupération des données:", response.status_code)
                return None
        df = pd.DataFrame(all_data, columns=['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time',
                                             'Quote Asset Volume', 'Number of Trades', 'Taker Buy Base Asset Volume',
                                             'Taker Buy Quote Asset Volume', 'ignore'])
        df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
        df['Close Time'] = pd.to_datetime(df['Close Time'], unit='ms')
        df.drop(['ignore'], axis=1, inplace=True)
        df = df[(df['Open Time'] >= start_time) & (df['Open Time'] < end_time)]
        return df

    def collect_all_data(self):
        for ticker in self.tickers:
            self.data[ticker] = self.collect_data(ticker=f"{ticker}USDT")
        return self.data


if __name__ == '__main__':
    data_collector = DataCollector(tickers=['BTC', 'ETH'], start_date='2022-01-01', end_date='2023-01-01', interval='1h')
    user_data = data_collector.collect_all_data()
    print(user_data)
