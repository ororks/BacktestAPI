import pandas as pd
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from pydantic import BaseModel
from Data_collector import DataCollector
import subprocess
import sys
import os
import json
import Backtest
from google.cloud import scheduler
from google.oauth2 import service_account
from google.cloud import storage
from typing import Optional
from google.api_core.exceptions import GoogleAPICallError, AlreadyExists
from datetime import datetime, timedelta
import re

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.relpath("boreal-forest-416815-c57cb5c11bdc.json", start=os.path.curdir)

app = FastAPI()

class UserInput(BaseModel):

    """
       Modèle de requête suivi par l'utilisateur :

       - func_strat : La fonction de trading en str renvoyant un poids pour chaque actif à chaque date.
       - requirements : Liste des imports nécessaires.
       - tickers : Liste des tickers considérés.
       - dates_test : Dates sur lesquelles on teste la stratégie de trading.
       - interval : Fréquence des observations considérées.
       - amount : Montant initial du portefeuille.
       - rqt_name : Nom de la requête pour identification.
       - repeat_frequency

       """
    func_strat: str
    requirements: list[str]
    tickers: list[str]
    dates: list[str]
    interval: str
    amount: str
    rqt_name: str
    is_recurring: bool
    repeat_frequency: int
    nb_execution: int
    current_execution_count: Optional[int]=0

#
# def check_scheduler(user_input: UserInput = Depends()) -> UserInput:
#     """
#     Dépendance qui check si la requête de l'utilisateur précise une
#     reprogrammation du backtest à des dates futures. Si c'est le cas,
#     is_recurring est passé en False pour que chaque réexecution depuis
#     google cloud ne programme pas elle même des réexécution.
#     """
#     if user_input.is_recurring:
#         modified_input = user_input.copy(update={"is_recurring": False})
#         scheduler = CloudScheduler(modified_input)
#         scheduler.save_request_to_storage()
#         scheduler.create_scheduler_job()
#         return modified_input
#     return user_input
#
#
# async def check_security(request: Request):
#     disallowed_patterns = [
#         re.compile(r"exec\s*\("),
#         re.compile(r"subprocess\.[a-zA-Z0-9_]"),
#     ]
#     response_check = await request.json()
#     func_strat_text = response_check.get("func_strat", "")
#     if any(pattern.search(func_strat_text) for pattern in disallowed_patterns):
#         raise HTTPException(status_code=400, detail="La requête contient des éléments dangereux.")
#     return


# Création de la route
@app.post('/backtesting/')
async def main(input: UserInput):
    """
    :param input: Données utilisateurs spécifiées dans le modèle User_input.
    :return: Les statistiques de backtest obtenues -> json
    Gère les appels aux différentes fonctions de l'architecture et le déroulement du backtest.
    - Récupère les données avec collect_APIdata() -> dictionnaire de pd.DataFrame
    - Ecrit la fonction utilisateur dans un .py temporaire
    - Converti en json les pd.DataFrame à l'intérieur du dictionnaire user_data
    - Ecrit les données dans un fichier .json temporaire
    - Appel de create_venv pour créer un environnement virtuel avec les packages requis
        par l'utilisateur. Run de sa fonction dans ce venv et récupération de l'output.
    - Appel de la fonction backtesting pour récupérer les statistiques.
    """

    data_collector = DataCollector(input.tickers, input.dates, input.interval)
    try:
        user_data = data_collector.collect_APIdata()
    except HTTPException as e:
        raise HTTPException(status_code=400, detail=f'erreur : {str(e)}')

    backtest_handler = BacktestHandler(input, user_data)
    stats_backtest = backtest_handler.run_backtest()

    return stats_backtest


class BacktestHandler:
    def __init__(self,
                 user_input: UserInput,
                 data: pd.DataFrame):
        self.user_input = user_input
        self.data = data

    @staticmethod
    def run_subprocess(*args, **kwargs):
        kwargs.setdefault('text', True)
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.PIPE)
        try:
            result = subprocess.run(args, check=True, **kwargs)
            if result.stderr:
                print(f"Subprocess stderr: {result.stderr}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Subprocess failed: {e.stderr}") from e

    def run_backtest(self):
        # Save du dataframe en json
        with open("user_function.py", "w") as file:
            file.write(self.user_input.func_strat)

        # Conversion de chaque df en json
        dico_df_json = {key: df.to_json() for key, df in self.data.items()}

        # Serialisation du dico en json et save dans un fichier
        with open("user_data.json", "w") as file:
            json.dump(dico_df_json, file)

        result_json = self.create_venv()
        # return type(result_json)
        result = pd.read_json(result_json, orient="index")

        stats_backtest = self.backtesting(result, self.data)
        os.remove(os.path.relpath("user_function.py", start=os.path.curdir))
        os.remove(os.path.relpath("user_data.json", start=os.path.curdir))
        return stats_backtest

    def create_venv(self):
        """
        - Run un sous-processus avec l'interpréteur python qui créé un venv avec pour nom la requête de l'utilisateur
        - Création du chemin vers le pip éxecutable pour le venv pour installer les packages
        - Run d'un sous-processus par packages pour leurs installation dans le venv
        - Création des paths vers les fichiers nécessaires (éxécutable, data, fonction, wrapper)
        - Run d'un sous-processus d'éxécution du module script_wrapper avec les arguments data_path et function_path
            Récupération des résultats de la fonction utilisateur par ce sous-processus -> pd.DataFrame
        """
        # Création de l'environnement virtuel
        BacktestHandler.run_subprocess(sys.executable, "-m", "venv", self.user_input.rqt_name)

        # Création du chemin vers le pip executable pour l'env virtuel
        pip_route = os.path.join(self.user_input.rqt_name, "Scripts" if os.name == "nt" else "bin", "pip")

        # Installation des packages
        for package in self.user_input.requirements:
            BacktestHandler.run_subprocess(pip_route, "install", package)

        python_executable = os.path.join(self.user_input.rqt_name, "Scripts" if os.name == "nt" else "bin", "python")
        function_path = os.path.relpath("user_function.py", start=os.path.curdir)
        wrapper_path = os.path.relpath("script_wrapper.py", start=os.path.curdir)
        data_path = os.path.relpath("user_data.json", start=os.path.curdir)
        response = BacktestHandler.run_subprocess(python_executable, wrapper_path, data_path, function_path, text=True)
        return response

    def backtesting(self, weights, dico_df):
        backtest = Backtest.Stats(weights, dico_df)
        stats_bt = backtest.to_json()
        return stats_bt



class CloudScheduler:
    def __init__(self,
                 user_input: UserInput):
        self.user_input = user_input


    def frequency_to_cron(self):
        if self.user_input.repeat_frequency == 1:
            return "0 0 * * *"  # À minuit chaque jour
        elif self.user_input.repeat_frequency == 7:
            return "0 0 * * 1"  # À minuit tous les lundis
        elif self.user_input.repeat_frequency == 30:
            return "0 0 1 * *"  # À minuit le premier jour de chaque mois
        else:
            raise ValueError("La fréquence spécifiée n'est pas supportée en format cron")

    def save_request_to_storage(self, bucket_name="backtestapi_bucket"):
        try:
            """Sauvegarde la requête de l'utilisateur dans un fichier JSON sur Cloud Storage."""
            # Transforme les données d'entrée en JSON
            user_input_dict = self.user_input.dict()
            dates = user_input_dict.get("dates")
            date_fin = datetime.strptime(dates[1], "%Y-%m-%d")
            date_fin = date_fin + timedelta(days=self.user_input.repeat_frequency)
            dates[1] = date_fin.strftime("%Y-%m-%d")
            user_input_dict["dates"] = dates
            data_to_save = json.dumps(user_input_dict).encode("utf-8")

            # Crée une instance du client de stockage
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)

            # Crée un nouvel objet blob dans le bucket
            file_name = self.user_input.rqt_name
            blob = bucket.blob(file_name)

            # Télécharge les données dans le blob
            blob.upload_from_string(data_to_save, content_type="application/json")

            print(f"Les données ont été sauvegardées dans {file_name} dans le bucket {bucket_name}.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données dans Cloud Storage: {e}")

    def create_scheduler_job(self, bucket_name="backtestapi_bucket"):
        credentials_path = os.path.relpath("boreal-forest-416815-c57cb5c11bdc.json", start=os.path.curdir)
        credentials = service_account.Credentials.from_service_account_file(credentials_path)

        project = 'boreal-forest-416815'
        location = 'europe-west1'
        parent = f'projects/{project}/locations/{location}'
        job_name = f'{self.user_input.rqt_name}'
        frequency = self.frequency_to_cron()

        client = scheduler.CloudSchedulerClient(credentials=credentials)
        function_url = "https://europe-west9-boreal-forest-416815.cloudfunctions.net/trigger_api"

        body = json.dumps({"bucket_name": bucket_name, "file_name": self.user_input.rqt_name}).encode('utf-8')

        job = {
            'name': f'{parent}/jobs/{job_name}',
            'http_target': {
                'uri': function_url,
                'http_method': scheduler.HttpMethod.POST,
                'body': body,
                'headers': {
                    'Content-Type': 'application/json'
                },
            },
                'schedule': frequency,
                'time_zone': 'Europe/Paris',
                'attempt_deadline': "600s"
        }

        try:
            response = client.create_job(request={"parent": parent, "job": job})
            print("Tâche créée : ", response.name)
            return response
        except AlreadyExists as e:
            print(f"Erreur : La tâche existe déjà - {e}")
            # Gérer le cas où la tâche existe déjà, si nécessaire.
        except GoogleAPICallError as e:
            print(f"Erreur lors de l'appel à l'API : {e}")
            # Gérer les erreurs d'appel API (erreurs réseau, erreurs de serveur, etc.)
        except Exception as e:
            print(f"Erreur inattendue : {e}")
            # Gérer toutes les autres exceptions inattendues.

