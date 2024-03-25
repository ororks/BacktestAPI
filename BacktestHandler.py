import Backtest
from main import UserInput
import pandas as pd
import subprocess
import os
import sys
import json

class BacktestHandler:
    """
    La classe BacktestHandler est destinée à orchestrer le processus de backtesting de stratégies de trading fournies
    par l'utilisateur. Elle utilise les données financières collectées et exécute le code de stratégie dans un
    environnement virtuel sécurisé pour évaluer sa performance.
    """
    def __init__(self,
                 user_input: UserInput,
                 data: pd.DataFrame):
        self.user_input = user_input
        self.data = data

    @staticmethod
    def run_subprocess(*args, **kwargs):
        """
        Description : Exécute une commande dans un sous-processus, capturant sa sortie standard et ses erreurs.
        Paramètres :
            *args : Arguments de la commande à exécuter dans le sous-processus.
            **kwargs : Arguments nommés optionnels, notamment pour la configuration du sous-processus.
        Renvoie : La sortie standard du sous-processus.
        """
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
        """
        Description : Coordonne le processus de backtesting en sauvegardant les données nécessaires,
        en créant un environnement virtuel, en exécutant le code de stratégie de l'utilisateur
        et en collectant les résultats.

        Renvoie : Les résultats du backtesting sous forme de données structurées.

        Processus :
            Sauvegarde la stratégie de trading de l'utilisateur et les données financières dans des fichiers temporaires.
            Crée un environnement virtuel et installe les packages requis.
            Exécute la stratégie de trading dans l'environnement virtuel et collecte les résultats.
            Nettoie les fichiers temporaires et renvoie les résultats du backtesting.
        """
        # Save du dataframe en json
        with open("user_function.py", "w") as file:
            file.write(self.user_input.func_strat)

        # Conversion de chaque df en json
        dico_df_json = {key: df.to_json() for key, df in self.data.items()}

        # Serialisation du dico en json et save dans un fichier
        with open("user_data.json", "w") as file:
            json.dump(dico_df_json, file)

        result_json = self.create_venv()
        result = pd.read_json(result_json, orient="index")

        stats_backtest = self.backtesting(result, self.data)
        os.remove(os.path.relpath("user_function.py", start=os.path.curdir))
        os.remove(os.path.relpath("user_data.json", start=os.path.curdir))
        return stats_backtest

    def create_venv(self):
        """
        Description : Crée un environnement virtuel Python, installe les packages requis par
        la stratégie de trading de l'utilisateur, et exécute la stratégie dans cet environnement.

        Renvoie : La sortie standard du sous-processus exécutant le code de la stratégie.

        Processus :
            Utilise Python pour créer un nouvel environnement virtuel.
            Installe les packages requis dans l'environnement virtuel.
            Prépare et exécute la stratégie de trading de l'utilisateur dans l'environnement virtuel.
        """
        # Création de l'environnement virtuel
        BacktestHandler.run_subprocess(sys.executable, "-m", "venv", self.user_input.request_id)

        # Création du chemin vers le pip executable pour l'env virtuel
        pip_route = os.path.join(self.user_input.request_id, "Scripts" if os.name == "nt" else "bin", "pip")

        # Installation des packages
        for package in self.user_input.requirements:
            BacktestHandler.run_subprocess(pip_route, "install", package)

        python_executable = os.path.join(self.user_input.request_id, "Scripts" if os.name == "nt" else "bin", "python")
        function_path = os.path.relpath("user_function.py", start=os.path.curdir)
        wrapper_path = os.path.relpath("script_wrapper.py", start=os.path.curdir)
        data_path = os.path.relpath("user_data.json", start=os.path.curdir)
        response = BacktestHandler.run_subprocess(python_executable, wrapper_path, data_path, function_path, text=True)
        return response

    def backtesting(self, weights, dico_df):
        """
        Description : Effectue le backtesting proprement dit en utilisant la bibliothèque Backtest
        sur les données et les poids (ou signaux) fournis.

        Paramètres :
            weights : Les poids ou signaux générés par la stratégie de trading de l'utilisateur.
            dico_df : Dictionnaire des DataFrames contenant les données financières utilisées pour le backtesting.
        Renvoie : Les statistiques de performance du backtesting sous forme de données structurées.
        """
        backtest = Backtest.Stats(weights, dico_df)
        stats_bt = backtest.to_json()
        return stats_bt
