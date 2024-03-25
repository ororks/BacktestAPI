import pandas as pd
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from pydantic import BaseModel, Field
from Data_collector import DataCollector
from BacktestHandler import BacktestHandler
from Cloudscheduler import CloudScheduler
from typing import Optional
import os
import re



app = FastAPI()


class UserInput(BaseModel):

    func_strat: str = Field(..., title="Votre fonction de trading",
                            description="""La fonction doit être en string directement dans la requête.
                                        Elle doit prendre en argument un DataFrame pandas et renvoyer un DataFrame
                                        pandas. Les imports nécessaires doivent être inclus au début du string.""",
                            example="""
                                    import pandas as pd
                                    def fonction_trading(df: pd.DataFrame):
                                    ....
                                    df_positions = pd.DataFrame()'
                                    return df_positions
                                    """)
    requirements: list[str] = Field(..., title="Packages requis pour votre fonction",
                                    description="""Ils doivent être fournis dans une liste de string. Seul le nom
                                                des packages permettant leur installation doit être fournis.""",
                                    example="['pandas', 'scipy']")
    tickers: list[str] = Field(..., title="Tickers des coins considérés",
                               description="""Les tickers des coins que vous souhaitez utiliser dans votre fonction
                                                "en liste de string""",
                               example="['ETHBTC', 'BNBETH']")
    dates: list[str] = Field(..., title="Dates considérées",
                             description="""Dates considérées pour les données en liste de string. Les dates doivent
                                         être données en format YYYY-MM-DD.""",
                             example="['2022-01-01', '2023-01-07']")
    interval: str = Field(..., title="Intervalle pour la fréquence des données.",
                          description= """Les intervalles disponibles sont : 
                                       1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M.""",
                          example="1d")
    request_id: str = Field(title="Identifiant de la requête",
                            description="""Identifiant unique de requête. Si une requête en cours à le même identifiant
                                        alors votre requête sera refusée.""",
                            example="rqt_250324")
    is_recurring: bool = Field(title="Option de programmation de backtests",
                               description="""Booléen pour indiquer si vous souhaitez reprogrammer un backtest de cette
                                           fonction de trading avec les nouvelles données apparues entre l'envoi de la 
                                           requête et la reprogrammation.""",
                               example="True")
    repeat_frequency: int = Field(title="Fréquence de réexécution",
                                  description="""Fréquences standardisées disponibles pour la réexécution de backtests
                                              d'une requête initiale avec les nouvelles données apparues.
                                              Les fréquences disponibles sont : 1, 7, 30 (en jours). La fréquence"
                                              choisie doit être indiquée comme un int.""",
                                  example="7")
    nb_execution: int = Field(title="Nombre de réexécution",
                              description="""Nombre de réexécutions de la requête intiale prorgammées avec les paramètres
                                          précédents. Ce nombre doit être précisé comme un entier int.""",
                              example="4")
    current_execution_count: Optional[int] = 0


async def check_security(request: Request):
    disallowed_patterns = [
        re.compile(r"exec\s*\("),
        re.compile(r"subprocess\.[a-zA-Z0-9_]"),
    ]
    response_check = await request.json()
    func_strat_text = response_check.get("func_strat", "")
    if any(pattern.search(func_strat_text) for pattern in disallowed_patterns):
        raise HTTPException(status_code=400, detail="La requête contient des éléments dangereux.")
    return


# Création de la route
@app.post('/backtesting/', description="""Réalise le backtest d'une fonction de stratégie de trading propre à
                                       l'utilisateur sur données de bougies de crypto-actifs.""")
async def main(input: UserInput, security_check: None=Depends(check_security)):
    """
    Endpoint du pour le backtesting de fonction de trading personnalisée.
    La requête doit respectée le modèle décrit dans la documentation.
    Processus :
        - Modification de la requête si is_recurring=True en False pour
        éviter les boucles infinies de programmation de réexécution.
        - Loading des données avec Data_collector
        - Instanciation de BacktestHandler
        - Run du backtest
    Renvoie : dictionnaire de stats calculées par la classe Stats de Backtest

    """
    if input.is_recurring:
        modified_input = input.copy(update={"is_recurring": False})
        scheduler = CloudScheduler(modified_input)
        scheduler.save_request_to_storage()
        scheduler.create_scheduler_job()

    data_collector = DataCollector(input.tickers, input.dates, input.interval)
    try:
        user_data = data_collector.collect_APIdata()
    except HTTPException as e:
        raise HTTPException(status_code=400, detail=f'erreur : {str(e)}')

    backtest_handler = BacktestHandler(input, user_data)
    stats_backtest = backtest_handler.run_backtest()

    return stats_backtest
