import json
import numpy as np
import pandas as pd
class Stats:
    """
    La classe Stats est conçue pour calculer et fournir des statistiques de performance
    pour une stratégie de trading sur les données financières. Elle utilise les poids de la
    stratégie et les données des actifs pour calculer différents indicateurs de performance,
    tels que le rendement annuel, la volatilité, le ratio de Sharpe, et plus encore.
    """
    def __init__(self, poids_ts, dfs_dict):
        self.poids_ts = poids_ts
        self.dfs_dict = dfs_dict
        self.rf_rate = 0.2
        self.scale = 9
        self.r_indice = self.calculate_index_returns()
        self.setup_metrics()

    def calculate_returns_from_dfs(self):
        """
        Description : Calcule les rendements à partir des DataFrames des prix de clôture des actifs.

        Renvoie : Un DataFrame des rendements calculés pour chaque actif.
        """
        df_closes = pd.DataFrame()
        df_concat = pd.DataFrame()
        for key, df in self.dfs_dict.items():
            df_closes = pd.DataFrame(df['Close'].items(), columns=['Date', key]).set_index('Date')
            df_closes[key] = df_closes[key].astype(float)
            df_concat = pd.concat([df_closes, df_concat], axis=1)
        df_returns = df_concat.pct_change().fillna(0)
        df_returns = df_returns.reset_index(drop=True)
        return df_returns

    def calculate_index_returns(self):
        """
        Description : Calcule les rendements de l'indice composé, basés sur
                    les poids de la stratégie et les rendements des actifs.

        Renvoie : Un DataFrame contenant les rendements de l'indice pour chaque période.
        """
        df_returns = self.calculate_returns_from_dfs()
        df_poids = self.poids_ts.reset_index(drop=True)
        df_index_returns = (df_returns * df_poids).sum(axis=1)
        return df_index_returns.to_frame(name='Index_Return')
        #return self.poids_ts
        #return df_returns

    def setup_metrics(self):
        """
        Description : Initialise les métriques de performance en calculant différentes statistiques
                        basées sur les rendements de l'indice.

        Rôle : Calcule et stocke les indicateurs clés de performance, comme le rendement annuel,
        la volatilité annuelle, le ratio de Sharpe, et d'autres statistiques.
        """
        self.r_annual = self.annualize_rets(self.r_indice, self.scale)
        self.vol_annual = self.annualize_vol()
        self.sharpe_r = self.sharpe_ratio()
        self.skew = self.skewness()
        self.kurt = self.kurtosis()
        self.semi_deviation = self.semideviation()
        self.var_hist = self.var_historic()
        self.max_draw = self.compute_drawdowns()
        self.downside_vol = self.downside_volatility()
        self.sortino_ratio = self.sortino_ratio()
        self.calmar_ratio = self.calmar_ratio()

    @staticmethod
    def annualize_rets(r, scale):
        compounded_growth = (1 + r).prod()
        n_periods = r.shape[0]
        return compounded_growth ** (scale / n_periods) - 1

    def annualize_vol(self):
        return self.r_indice.std() * np.sqrt(self.scale)

    def sharpe_ratio(self):
        rf_per_period = (1 + self.rf_rate) ** (1 / self.scale) - 1
        excess_ret = self.r_indice - rf_per_period
        return self.annualize_rets(excess_ret, self.scale) / self.annualize_vol()

    def skewness(self):
        demeaned_r = self.r_indice - self.r_indice.mean()
        return (demeaned_r ** 3).mean() / (self.r_indice.std(ddof=0) ** 3)

    def kurtosis(self):
        demeaned_r = self.r_indice - self.r_indice.mean()
        return (demeaned_r ** 4).mean() / (self.r_indice.std(ddof=0) ** 4)

    def semideviation(self):
        return self.r_indice[self.r_indice < 0].std(ddof=0)

    def var_historic(self, level=5):
        return np.percentile(self.r_indice, level)

    def compute_drawdowns(self):
        peaks = self.r_indice.cummax()
        drawdowns = (self.r_indice - peaks) / peaks
        return drawdowns.min()

    def downside_volatility(self):
        downside = np.minimum(self.r_indice - self.rf_rate, 0)
        return np.sqrt(np.mean(downside ** 2))

    def sortino_ratio(self):
        rf_per_period = (1 + self.rf_rate) ** (1 / self.scale) - 1
        excess_return = self.r_indice - rf_per_period
        return self.annualize_rets(excess_return, self.scale) / self.downside_volatility()

    def calmar_ratio(self):
        return self.r_annual / -self.max_draw

    def to_json(self):
        """
        Description : Convertit les statistiques de performance calculées en une chaîne JSON formatée.

        Renvoie : Une chaîne JSON contenant toutes les métriques de performance calculées par l'instance Stats.
        """
        stats_dict = {
            'Rendement Annuel': self.r_annual.item() if isinstance(self.r_annual, pd.Series) else self.r_annual,
            'Volatilite Annuelle': self.vol_annual.item() if isinstance(self.vol_annual,
                                                                        pd.Series) else self.vol_annual,
            'Ratio de Sharpe': self.sharpe_r.item() if isinstance(self.sharpe_r, pd.Series) else self.sharpe_r,
            'Skewness': self.skew.item() if isinstance(self.skew, pd.Series) else self.skew,
            'Kurtosis': self.kurt.item() if isinstance(self.kurt, pd.Series) else self.kurt,
            'Semi-Deviation': self.semi_deviation.item() if isinstance(self.semi_deviation,
                                                                       pd.Series) else self.semi_deviation,
            'VaR Historique': self.var_hist.item() if isinstance(self.var_hist, pd.Series) else self.var_hist,
            'Drawdown Maximal': self.max_draw.item() if isinstance(self.max_draw, pd.Series) else self.max_draw,
            'Volatilite a la Baisse': self.downside_vol.item() if isinstance(self.downside_vol,
                                                                             pd.Series) else self.downside_vol,
            'Ratio de Sortino': self.sortino_ratio.item() if isinstance(self.sortino_ratio,
                                                                        pd.Series) else self.sortino_ratio,
            'Ratio de Calmar': self.calmar_ratio.item() if isinstance(self.calmar_ratio,
                                                                      pd.Series) else self.calmar_ratio
        }
        return json.dumps(stats_dict, indent=4)


if __name__ == "__main__":

    statistiques = Stats()