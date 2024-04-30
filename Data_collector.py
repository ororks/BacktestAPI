import pandas as pd
import requests
from datetime import datetime, timezone

class DataCollector:
    """
    La classe DataCollector est conçue pour collecter des données financières depuis une API externe.
    Elle permet de récupérer des données historiques de prix pour une liste spécifiée de tickers (symboles d'actifs)
    sur une période donnée et à une fréquence définie.
    """
    def __init__(self, tickers_list: list[str], dates_list: list[str], interval:str):
        self.tickers_list = tickers_list
        self.dates_list = dates_list
        self.interval = interval
        self.data = {}

    def collect_APIdata(self):
        """
        Description : Collecte les données historiques de prix pour chaque ticker spécifié dans tickers_list,
        sur la période définie par dates_list et avec l'intervalle spécifié par interval.

        Renvoie : Un dictionnaire où chaque clé correspond à un ticker et chaque valeur est un DataFrame pandas
        contenant les prix de clôture des actifs correspondants, indexés par date.

        Processus :
            Construit une URL de requête pour accéder à l'API externe.
            Convertit les dates de début et de fin en timestamps UNIX (en millisecondes) compatibles avec l'API.
            Pour chaque ticker dans tickers_list, effectue une requête GET à l'API avec les paramètres appropriés
            pour récupérer les données historiques.
            Transforme les données reçues en un DataFrame pandas, sélectionne les colonnes pertinentes
            (ici, uniquement le prix de clôture et les dates), et les index par date.
            Stocke le DataFrame résultant dans le dictionnaire data.

        """
        url = "https://data-api.binance.vision/api/v3/klines"
        start_date = datetime.strptime(self.dates_list[0], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        start_date = int(start_date.timestamp() * 1000)
        end_date = datetime.strptime(self.dates_list[1], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_date = int(end_date.timestamp() * 1000)
        for symbol in self.tickers_list:
            params = {
                'symbol': symbol,
                'interval': self.interval,
                'startTime': start_date,
                'endTime': end_date
            }
            response = requests.get(url, params=params)
            data = response.json()
            df = pd.DataFrame(data, columns=['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time',
                                             'Quote_volume', 'Nb_trades', 'ignore1', 'ignore2', 'ignore3'])
            df['Dates'] = pd.to_datetime(df['Open_time'], unit='ms')
            df = df[['Close']].set_index(df['Dates'])
            self.data[symbol] = df
        return self.data

#######################################       TEST       ##############################################################

if __name__ == '__main__':
    data_collector = DataCollector(tickers_list=['ETHBTC', 'BNBETH'], dates_list=['2023-01-01', '2023-01-02'], interval='1d')
    user_data = data_collector.collect_APIdata()
    print(user_data)