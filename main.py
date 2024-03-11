import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from Data_collector import DataCollector
import subprocess
import sys
import os
import json
import Backtest
from google.cloud import scheduler
from google.oauth2 import service_account
import google.cloud.storage
import requests
from google.cloud import storage


app = FastAPI()
class User_input(BaseModel):
    """
       Modèle de requête suivi par l'utilisateur :

       - func_strat : La fonction de trading en str renvoyant un poids pour chaque actif à chaque date.
       - requirements : Liste des imports nécessaires.
       - tickers : Liste des tickers considérés.
       - dates_calibration : Dates pour calibrer la fonction de stratégie.
       - dates_test : Dates sur lesquelles on teste la stratégie de trading.
       - interval : Fréquence des observations considérées.
       - amount : Montant initial du portefeuille.
       - rqt_name : Nom de la requête pour identification.

       """
    func_strat: str
    requirements: list[str]
    tickers: list[str]
    dates_calibration: list[str]
    interval: str
    amount: str
    rqt_name : str
    # repeat_frequency: str

# Création de la route
@app.post('/backtesting/')

async def main(input: User_input):
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
    data_collector = DataCollector(input.tickers, input.dates_calibration, input.interval)
    try:
        user_data = data_collector.collect_APIdata()
    except HTTPException as e:
        raise HTTPException(status_code=400, detail=f'erreur : {str(e)}')

    # Save du dataframe en json
    with open("user_function.py", "w") as file:
        file.write(input.func_strat)

    # Conversion de chaque df en json
    dico_df_json = {key: df.to_json() for key, df in user_data.items()}

    # Serialisation du dico en json et save dans un fichier
    with open("user_data.json", "w") as file:
        json.dump(dico_df_json, file)

    # with open("user_request.json", "w") as file:
    #     file.write(input)

    result_json = create_venv(input.rqt_name, input.requirements, "user_function.py")
    # return type(result_json)
    result = pd.read_json(result_json, orient="index")

    stats_backtest = backtesting(result, user_data)
    os.remove(os.path.abspath("user_function.py"))
    os.remove(os.path.abspath("user_data.json"))
    return stats_backtest

def create_venv(name, packages, funct):
    """
    :param name: Nom de la requête de l'utilisateur pour identification.
    :param packages: packages donnés en input dans la requête de l'utilisateur.
    :param funct: fonction donnée en input dans la requête de l'utilisateur.
    :return: l'output défini par la fonction de l'utilisateur.
    - Run un sous-processus avec l'interpréteur python qui créé un venv avec pour nom la requête de l'utilisateur
    - Création du chemin vers le pip éxecutable pour le venv pour installer les packages
    - Run d'un sous-processus par packages pour leurs installation dans le venv
    - Création des paths vers les fichiers nécessaires (éxécutable, data, fonction, wrapper)
    - Run d'un sous-processus d'éxécution du module script_wrapper avec les arguments data_path et function_path
        Récupération des résultats de la fonction utilisateur par ce sous-processus -> pd.DataFrame
    """
    # Création de l'environnement virtuel
    run_subprocess(sys.executable, "-m", "venv", name)

    # Création du chemin vers le pip executable pour l'env virtuel
    pip_route = os.path.join(name, "Scripts" if os.name == "nt" else "bin", "pip")

    # Installation des packages
    for package in packages:
        run_subprocess(pip_route, "install", package)
    #
    python_executable = os.path.join(name, "Scripts" if os.name == "nt" else "bin", "python")
    function_path = os.path.abspath(funct)
    wrapper_path = os.path.abspath("script_wrapper.py")
    data_path = os.path.abspath("user_data.json")
    response = run_subprocess(python_executable, wrapper_path, data_path, function_path, capture_output=True, text=True)
    return response


def backtesting(weights, dico_df):
    backtest = Backtest.Stats(weights, dico_df)
    stats_bt = backtest.to_json()
    return stats_bt

def run_subprocess(*args, **kwargs):
    try:
        result = subprocess.run(args, check=True, **kwargs)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Erreur dans l'éxécution du sous-processus : {e}"

#
# def frequency_to_cron(repeat_frequency):
#     # Dictionnaire de correspondance fréquence vers cron
#     frequency_cron_map = {
#         "1d": "0 0 * * *",  # À minuit chaque jour
#         "7d": "0 0 * * 1",  # À minuit tous les lundis (exemple pour "tous les 7 jours")
#     }
#
#     # Pour les fréquences mensuelles, on gère séparément car il n'y a pas de code direct
#     if repeat_frequency == "1m":
#         return "0 0 1 * *"  # À minuit le premier jour de chaque mois
#
#     # Retourne la valeur cron correspondante ou une valeur par défaut si non trouvée
#     return frequency_cron_map.get(repeat_frequency, "0 0 * * *")  # Par défaut chaque jour à minuit
#
#
# # Exemple d'utilisation
# # repeat_frequency = "1d"  # Exemple d'entrée utilisateur
# # cron_schedule = frequency_to_cron(repeat_frequency)
# # print(cron_schedule)  # "0 0 * * *"
#
# def save_request_to_storage(user_input:User_input, bucket_name="backtestapi_bucket", file_name="user_request"):
#     """Sauvegarde la requête de l'utilisateur dans un fichier JSON sur Cloud Storage."""
#     # Transforme les données d'entrée en JSON
#     data_to_save = json.dumps(user_input.dict()).encode("utf-8")
#
#     # Crée une instance du client de stockage
#     storage_client = storage.Client()
#     bucket = storage_client.bucket(bucket_name)
#
#     # Crée un nouvel objet blob dans le bucket
#     blob = bucket.blob(file_name)
#
#     # Télécharge les données dans le blob
#     blob.upload_from_string(data_to_save, content_type="application/json")
#
#     print(f"Les données ont été sauvegardées dans {file_name} dans le bucket {bucket_name}.")
#
#
# def create_scheduler_job(input: User_input, bucket_name, file_name):
#     # Assurez-vous d'avoir importé les bibliothèques nécessaires et configuré les variables
#     # Supposons que 'input' est maintenant un objet avec les attributs nécessaires pour cette tâche
#
#     # Chemin vers votre fichier clé JSON pour l'authentification
#     credentials_path = os.path.abspath("boreal-forest-416815-c57cb5c11bdc.json")
#     credentials = service_account.Credentials.from_service_account_file(credentials_path)
#
#     # Paramètres du projet et de la tâche
#     project = 'boreal-forest-416815'
#     location = 'europe-west1'
#     parent = f'projects/{project}/locations/{location}'
#     job_name = f'{input.rqt_name}'  # Assurez-vous que cela est unique
#     frequency = frequency_to_cron(input.repeat_frequency)  # Fonction pour convertir la fréquence
#
#     # Client Cloud Scheduler
#     client = scheduler_v1.CloudSchedulerClient(credentials=credentials)
#     # Configuration de l'URL de déclenchement de la fonction Cloud Functions
#     function_url = "https://us-central1-boreal-forest-416815.cloudfunctions.net/trigger_api"
#     # Création du corps de la requête, qui inclut le nom du bucket et le nom du fichier
#     body = json.dumps({"bucket_name": bucket_name, "file_name": file_name}).encode('utf-8')
#
#     # Configuration de la tâche
#     job = {
#         # Remarque : Pas besoin de préciser 'name', Cloud Scheduler attribuera un nom unique à la tâche
#         'http_target': {
#             'uri': function_url,
#             'http_method': scheduler_v1.HttpMethod.POST,
#             'body': body,
#             'headers': {
#                 'Content-Type': 'application/json'
#             },
#         },
#         'schedule': frequency,
#         'time_zone': 'Europe/Paris',  # Ou votre fuseau horaire approprié
#     }
#
#     # Création de la tâche
#     response = client.create_job(request={"parent": parent, "job": job})
#     print("Tâche créée : ", response.name)
