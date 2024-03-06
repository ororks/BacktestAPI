import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from Data_collector import collect_APIdata
import subprocess
import sys
import os
import json
import Backtest



app = FastAPI()
class User_input(BaseModel):
    """
    Modèle de requête suivi par l'utilisateur :
    func_strat : La fonction de trading de l'utilisateur en str qui renvoie un poids dans pour chaque actifs à chaque
    date dans le portefeuille
    requirements : liste des imports
    tickers : liste des tickers considérés
    dates_calibrations : liste des dates pour calibrer la fonction de stratégie
    dates_test : dates sur lesquels ont teste la stratégie de trading
    interval : fréquence des observations considérées
    amount : montant du portefeuille
    """
    func_strat: str
    requirements: list[str]
    tickers: list[str]
    dates_calibration: list[str]
    dates_test : list[str]
    interval: str
    amount: str
    rqt_name : str

# Création de la route
@app.post('/backtesting/')
async def main(input: User_input):
    try:
        user_data = collect_APIdata(input.tickers, input.dates_calibration, input.interval)
    except HTTPException as e:
        raise HTTPException(status_code=400, detail=f'erreur : {str(e)}')

    # # save du dataframe en json
    # user_data.to_json("user_data.json", orient="index", date_format="iso", indent=4)
    #
    with open("user_function.py", "w") as file:
        file.write(input.func_strat)

    # Conversion de chaque df en json
    dico_df_json = {key: df.to_json() for key, df in user_data.items()}
    # Serialisation du dico en json et save dans un fichier
    with open("user_data.json", "w") as file:
        json.dump(dico_df_json, file)

    result_json = create_venv(input.rqt_name, input.requirements, "user_function.py")
    result = pd.read_json(result_json, orient="index")
    # return user_data
    stats_backtest = backtesting(result, user_data)
    return stats_backtest
    # except Exception as e:
    #     print(f"erreur : {e}")



def create_venv(name, packages, funct):
    # Création de l'environnement virtuel
    try:
        subprocess.run([sys.executable, "-m", "venv", name], check=True)
    except subprocess.CalledProcessError as e:
        print(f'erreur : {str(e)}')

    # Création du chemin vers le pip executable pour l'env virtuel
    pip_route = os.path.join(name, "Scripts" if os.name == "nt" else "bin", "pip")

    # Installation des packages
    try:
        for package in packages:
            subprocess.run([pip_route, "install", package], check=True)
    except subprocess.CalledProcessError as e:
        print(f'erreur : {str(e)}')

    #
    python_executable = os.path.join(name, "Scripts" if os.name == "nt" else "bin", "python")
    function_path = os.path.abspath(funct)
    wrapper_path = os.path.abspath("script_wrapper.py")
    data_path = os.path.abspath("user_data.json")
    try:
        result = subprocess.run([python_executable, wrapper_path, data_path, function_path], capture_output=True, check=True, text=True)
        response = result.stdout
        print(response)
    except subprocess.CalledProcessError as e:
        error = e.stderr
        print(error)
        return error
    return response


def backtesting(weights, dico_df):
    backtest = Backtest.Stats(weights, dico_df)
    stats_bt = backtest.to_json()
    return stats_bt

