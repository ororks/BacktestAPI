import importlib.util
import json
import sys
import pandas as pd
from typing import Dict

class Wrapper:
    """
    La classe Wrapper est conçue pour encapsuler le processus de chargement des données financières et
    d'exécution d'une fonction de stratégie de trading spécifiée par l'utilisateur.
    Elle permet d'isoler et d'exécuter de manière sécurisée le code utilisateur en fournissant une interface
    standardisée pour l'interaction avec les données.
    """
    def __init__(self, file_path: str, function_path: str):
        self.file_path = file_path
        self.function_path = function_path
        self.data_result = None
        self.function_result = None

    def load_data(self):
        """
        Description : Charge les données financières à partir du fichier JSON spécifié lors de l'initialisation.

        Renvoie : Un dictionnaire où chaque clé correspond à un identifiant d'actif et chaque valeur
        est un DataFrame pandas contenant les données financières pour cet actif.

        Processus :
            Ouvre et lit le contenu du fichier JSON spécifié par file_path.
            Convertit les données JSON en dictionnaire de DataFrames pandas, où chaque DataFrame représente les données
            financières d'un actif spécifique.
        """
        with open(self.file_path, "r") as file:
            dico_df_json = json.load(file)
        self.data_result = {key: pd.read_json(df_json) for key, df_json in dico_df_json.items()}
        return self.data_result

    def fonction_run(self):
        """
        Description : Charge et exécute la fonction de stratégie de trading de l'utilisateur sur les données
        financières chargées, puis convertit le résultat en format JSON.

        Renvoie : Le résultat de l'exécution de la fonction de stratégie de trading sous forme de chaîne JSON.

        Processus :
            Charge les données financières en appelant load_data().
            Utilise importlib pour charger dynamiquement le script de la fonction de trading de
            l'utilisateur spécifié par function_path.
            Exécute la fonction de stratégie de trading sur les données chargées et stocke le résultat.
            Convertit le résultat (un DataFrame pandas) en JSON.
        """
        self.data_result = self.load_data()
        # Création des spécifications du module à partir du path de la fonction enregistrée en json
        spec = importlib.util.spec_from_file_location("function_module", self.function_path)
        # Création du module à partir des specs
        function_module = importlib.util.module_from_spec(spec)
        # Chargement du module
        spec.loader.exec_module(function_module)
        results = function_module.func_strat(self.data_result)
        self.function_result = results.to_json(orient="index")
        return self.function_result

if __name__=="__main__":
    data_file_path = sys.argv[1]  # Chemin vers le fichier de données JSON.
    user_func_path = sys.argv[2]  # Chemin vers le script de l'utilisateur.
    wrapper = Wrapper(file_path=data_file_path, function_path=user_func_path)
    results = wrapper.fonction_run()
    # Indipensable d'avoir un print pour récuperer le résultat dans le subprocess
    print(results)


