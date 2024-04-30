# Documentation de l'API FastAPI pour le Backtesting de Stratégies de Trading (Utilisateur)

Une documentation est également disponible à :
https://backtestapi.onrender.com/redoc

## Endpoint : /backtesting/

### Description
Réalise le backtest d'une fonction de stratégie de trading propre à l'utilisateur sur données de bougies de crypto-actifs.
Le fichier client.py permet de tester l'API.

## Temps de chargement des résultats
Si le serveur est en veille avant la requête de l'utilisateur, celle ci peut prendre quelques minutes le temps que
que le serveur redémarre.

### Corps de la Requête (Request Body)

#### UserInput

- **func_strat** (`string`): Votre fonction de trading
  - **Description**: La fonction doit être en string directement dans la requête. Elle doit prendre en argument un DataFrame pandas et renvoyer un DataFrame pandas. Les imports nécessaires doivent être inclus au début du string.
  - **Exemple**:
    ```python
    import pandas as pd
    def fonction_trading(df: pd.DataFrame):
        # Votre logique de trading ici
        df_positions = pd.DataFrame()
        return df_positions
    ```

- **requirements** (`list[string]`): Packages requis pour votre fonction
  - **Description**: Ils doivent être fournis dans une liste de string. Seul le nom des packages permettant leur installation doit être fournis.
  - **Exemple**: `['pandas', 'scipy']`

- **tickers** (`list[string]`): Tickers des coins considérés
  - **Description**: Les tickers des coins que vous souhaitez utiliser dans votre fonction en liste de string.
  - **Exemple**: `['ETHBTC', 'BNBETH']`

- **dates** (`list[string]`): Dates considérées
  - **Description**: Dates considérées pour les données en liste de string. Les dates doivent être données en format YYYY-MM-DD.
  - **Exemple**: `['2022-01-01', '2023-01-07']`

- **interval** (`string`): Intervalle pour la fréquence des données.
  - **Description**: Les intervalles disponibles sont : 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M.
  - **Exemple**: `1d`

- **request_id** (`string`): Identifiant de la requête
  - **Description**: Identifiant unique de requête. Si une requête en cours à le même identifiant alors votre requête sera refusée.
  - **Exemple**: `rqt_250324`

- **is_recurring** (`boolean`): Option de programmation de backtests
  - **Description**: Booléen pour indiquer si vous souhaitez reprogrammer un backtest de cette fonction de trading avec les nouvelles données apparues entre l'envoi de la requête et la reprogrammation.
  - **Exemple**: `True`

- **repeat_frequency** (`integer`): Fréquence de réexécution
  - **Description**: Fréquences standardisées disponibles pour la réexécution de backtests d'une requête initiale avec les nouvelles données apparues. Les fréquences disponibles sont : 1, 7, 30 (en jours). La fréquence choisie doit être indiquée comme un int.
  - **Exemple**: `7`

- **nb_execution** (`integer`): Nombre de réexécution
  - **Description**: Nombre de réexécutions de la requête initiale programmées avec les paramètres précédents. Ce nombre doit être précisé comme un entier int.
  - **Exemple**: `4`

- **current_execution_count** (`integer`, optionnel): Compte actuel d'exécution
  - **Valeur par défaut**: `0`
  - **Note**: Ce champ est utilisé pour le suivi interne du nombre d'exécutions et n'est pas destiné à être modifié directement par l'utilisateur.

### Réponses

- **200 Successful Response**: La requête a réussi et le backtest a été réalisé.
- **422 Validation Error**: Erreur de validation des données envoyées dans la requête.

## Endpoint : /get_result
La route **get_result** permet de récupérer les résultats d'une requête donc la rééxécution a été programmée.
Les résultats ont donc été stockés dans un bucket google cloud storage. 

### Corps de la Requête (Request Body)
- **request_id** correspond 
à l'ID de requête utilisée lors de la requête initiale sur la route **/backtesting/**. Le fichier client permet
de tester cette fonctionnalité avec une requête déjà enregistrée sur le bucket.

# Documentation Interne pour les Développeurs

## Endpoint Principal : `/backtesting/`

### `async def main(input: UserInput, security_check: None=Depends(check_security)):`

- **Objectif** : Endpoint pour le backtesting de fonction de trading personnalisée. 
- **Processus** :
  - Modifie la requête si `is_recurring=True` en `False` pour éviter les boucles infinies de programmation de réexécution.
  - Charge les données avec `Data_collector`.
  - Instancie `BacktestHandler`.
  - Exécute le backtesting.
- **Renvoie** : Un dictionnaire des statistiques calculées par la classe `Stats` de Backtest.

## Classe : `BacktestHandler`

### Description Générale

La classe `BacktestHandler` orchestre le processus de backtesting des stratégies de trading fournies par l'utilisateur, utilisant les données financières collectées et exécutant le code de stratégie dans un environnement virtuel sécurisé pour évaluer sa performance.

### Méthodes

#### `def run_subprocess(*args, **kwargs):`

- **Description** : Exécute une commande dans un sous-processus, capturant sa sortie standard et ses erreurs.
- **Paramètres** :
  - `*args` : Arguments de la commande à exécuter dans le sous-processus.
  - `**kwargs` : Arguments nommés optionnels, notamment pour la configuration du sous-processus.
- **Renvoie** : La sortie standard du sous-processus.

#### `def run_backtest(self):`

- **Description** : Coordonne le processus de backtesting en sauvegardant les données nécessaires, créant un environnement virtuel, exécutant le code de stratégie de l'utilisateur et collectant les résultats.
- **Renvoie** : Les résultats du backtesting sous forme de données structurées.
- **Processus** :
  - Sauvegarde la stratégie de trading de l'utilisateur et les données financières dans des fichiers temporaires.
  - Crée un environnement virtuel et installe les packages requis.
  - Exécute la stratégie de trading dans l'environnement virtuel et collecte les résultats.
  - Nettoie les fichiers temporaires et renvoie les résultats du backtesting.

#### `def create_venv(self):`

- **Description** : Crée un environnement virtuel Python, installe les packages requis par la stratégie de trading de l'utilisateur, et exécute la stratégie dans cet environnement.
- **Renvoie** : La sortie standard du sous-processus exécutant le code de la stratégie.
- **Processus** :
  - Utilise Python pour créer un nouvel environnement virtuel.
  - Installe les packages requis dans l'environnement virtuel.
  - Prépare et exécute la stratégie de trading de l'utilisateur dans l'environnement virtuel.

#### `def backtesting(self, weights, dico_df):`

- **Description** : Effectue le backtesting proprement dit en utilisant la bibliothèque Backtest sur les données et les poids (ou signaux) fournis.
- **Paramètres** :
  - `weights` : Les poids ou signaux générés par la stratégie de trading de l'utilisateur.
  - `dico_df` : Dictionnaire des DataFrames contenant les données financières utilisées pour le backtesting.
- **Renvoie** : Les statistiques de performance du backtesting sous forme de données structurées.

## Classe : `DataCollector`

### Description Générale

La classe `DataCollector` est conçue pour collecter des données financières depuis une API externe. Elle permet de récupérer des données historiques de prix pour une liste spécifiée de tickers (symboles d'actifs) sur une période donnée et à une fréquence définie.

### Méthodes

#### `def __init__(self, tickers_list: list[str], dates_list: list[str], interval: str):`

- **Paramètres** :
  - `tickers_list` : Liste des tickers (symboles d'actifs) pour lesquels les données doivent être collectées.
  - `dates_list` : Liste contenant les dates de début et de fin de la période pour laquelle les données doivent être collectées, au format `YYYY-MM-DD`.
  - `interval` : Fréquence à laquelle les données doivent être collectées (par exemple, "1d" pour journalier).
- **Action** : Initialise une instance de `DataCollector` avec les listes de tickers, les dates et l'intervalle spécifiés.

#### `def collect_APIdata(self):`

- **Description** : Collecte les données historiques de prix pour chaque ticker spécifié dans `tickers_list`, sur la période définie par `dates_list` et avec l'intervalle spécifié par `interval`.
- **Renvoie** : Un dictionnaire où chaque clé correspond à un ticker et chaque valeur est un DataFrame pandas contenant les prix de clôture des actifs correspondants, indexés par date.
- **Processus** :
  - Construit une URL de requête pour accéder à l'API externe.
  - Convertit les dates de début et de fin en timestamps UNIX (en millisecondes) compatibles avec l'API.
  - Pour chaque ticker dans `tickers_list`, effectue une requête GET à l'API avec les paramètres appropriés pour récupérer les données historiques.
  - Transforme les données reçues en un DataFrame pandas, sélectionne les colonnes pertinentes (ici, uniquement le prix de clôture et les dates), et les indexe par date.
  - Stocke le DataFrame résultant dans le dictionnaire `data`.

## Classe : `Wrapper`

### Description Générale

La classe `Wrapper` est conçue pour encapsuler le processus de chargement des données financières et d'exécution d'une fonction de stratégie de trading spécifiée par l'utilisateur. Elle permet d'isoler et d'exécuter de manière sécurisée le code utilisateur en fournissant une interface standardisée pour l'interaction avec les données.

### Méthodes

#### `def __init__(self, file_path: str, function_path: str):`

- **Paramètres** :
  - `file_path` : Chemin vers le fichier JSON contenant les données financières.
  - `function_path` : Chemin vers le fichier contenant le script de la fonction de stratégie de trading de l'utilisateur.
- **Action** : Initialise une instance de `Wrapper` avec les chemins vers les données et la fonction de stratégie spécifiés.

#### `def load_data(self):`

- **Description** : Charge les données financières à partir du fichier JSON spécifié lors de l'initialisation.
- **Renvoie** : Un dictionnaire où chaque clé correspond à un identifiant d'actif et chaque valeur est un DataFrame pandas contenant les données financières pour cet actif.
- **Processus** :
  - Ouvre et lit le contenu du fichier JSON spécifié par `file_path`.
  - Convertit les données JSON en dictionnaire de DataFrames pandas, où chaque DataFrame représente les données financières d'un actif spécifique.

#### `def fonction_run(self):`

- **Description** : Charge et exécute la fonction de stratégie de trading de l'utilisateur sur les données financières chargées, puis convertit le résultat en format JSON.
- **Renvoie** : Le résultat de l'exécution de la fonction de stratégie de trading sous forme de chaîne JSON.
- **Processus** :
  - Charge les données financières en appelant `load_data()`.
  - Utilise `importlib` pour charger dynamiquement le script de la fonction de trading de l'utilisateur spécifié par `function_path`.
  - Exécute la fonction de stratégie de trading sur les données chargées et stocke le résultat.
  - Convertit le résultat (un DataFrame pandas) en JSON.


## Classe : `Stats`

### Description Générale

La classe `Stats` est conçue pour calculer et fournir des statistiques de performance pour une stratégie de trading sur les données financières. Elle utilise les poids de la stratégie et les données des actifs pour calculer différents indicateurs de performance, tels que le rendement annuel, la volatilité, le ratio de Sharpe, et plus encore.

### Méthodes

#### `def __init__(self, poids_ts, dfs_dict):`

- **Paramètres** :
  - `poids_ts` : Les poids attribués à chaque actif dans la stratégie de trading, souvent représentés par un DataFrame.
  - `dfs_dict` : Un dictionnaire des DataFrames contenant les prix de clôture pour chaque actif.
- **Action** : Initialise une instance de `Stats` avec les poids et les données financières spécifiés. Calcule également les rendements de l'indice basés sur les poids de la stratégie.

#### `def calculate_returns_from_dfs(self):`

- **Description** : Calcule les rendements à partir des DataFrames des prix de clôture des actifs.
- **Renvoie** : Un DataFrame des rendements calculés pour chaque actif.

#### `def calculate_index_returns(self):`

- **Description** : Calcule les rendements de l'indice composé, basés sur les poids de la stratégie et les rendements des actifs.
- **Renvoie** : Un DataFrame contenant les rendements de l'indice pour chaque période.

#### `def setup_metrics(self):`

- **Description** : Initialise les métriques de performance en calculant différentes statistiques basées sur les rendements de l'indice.
- **Rôle** : Calcule et stocke les indicateurs clés de performance, comme le rendement annuel, la volatilité annuelle, le ratio de Sharpe, et d'autres statistiques.

#### `def to_json(self):`

- **Description** : Convertit les statistiques de performance calculées en une chaîne JSON formatée.
- **Renvoie** : Une chaîne JSON contenant toutes les métriques de performance calculées par l'instance `Stats`.


## Classe : `CloudScheduler`

### Description Générale

La classe `CloudScheduler` permet de planifier et de gérer l'exécution automatisée de requêtes utilisateur dans le Cloud. Elle utilise Google Cloud Scheduler pour configurer des tâches planifiées qui déclenchent des fonctions Cloud, permettant ainsi l'exécution récurrente des requêtes de backtesting de stratégies de trading à des intervalles prédéfinis.

### Méthodes

#### `def __init__(self, user_input):`

- **Paramètres** :
  - `user_input` : L'objet contenant les données de la requête de l'utilisateur.
- **Action** : Initialise une instance de `CloudScheduler` avec les informations de la requête utilisateur.

#### `def frequency_to_cron(self):`

- **Description** : Convertit la fréquence de réexécution spécifiée par l'utilisateur en une expression cron compatible avec Google Cloud Scheduler.
- **Renvoie** : Une chaîne de caractères représentant l'expression cron correspondant à la fréquence de réexécution souhaitée.

#### `def save_request_to_storage(self, bucket_name="backtestapi_bucket"):`

- **Description** : Sauvegarde la requête de l'utilisateur dans un fichier JSON sur Google Cloud Storage pour une utilisation ultérieure par la fonction Cloud déclenchée.
- **Paramètres** :
  - `bucket_name` : Nom du bucket Cloud Storage où le fichier JSON sera sauvegardé.
- **Processus** :
  - Convertit les données de requête utilisateur en JSON.
  - Utilise le client Cloud Storage pour créer ou mettre à jour un objet blob contenant les données de la requête dans le bucket spécifié.

#### `def create_scheduler_job(self, bucket_name="backtestapi_bucket"):`

- **Description** : Crée une tâche planifiée dans Google Cloud Scheduler pour exécuter la requête utilisateur à l'heure et à la fréquence spécifiées.
- **Paramètres** :
  - `bucket_name` : Nom du bucket Cloud Storage où les données de la requête utilisateur sont stockées.
- **Processus** :
  - Construit une requête pour créer une nouvelle tâche dans Google Cloud Scheduler, incluant l'URL de la fonction Cloud à déclencher, l'expression cron pour la planification, et les données de la requête.
  - Utilise le client Cloud Scheduler pour soumettre la requête de création de tâche.

## Fonction Cloud : `trigger_api`

### Description Générale

Cette fonction Cloud est conçue pour être déclenchée à des intervalles prédéfinis par Google Cloud Scheduler. Son objectif principal est de réexécuter les requêtes de backtesting stockées dans Google Cloud Storage, permettant ainsi une exécution automatisée et récurrente des stratégies de trading à l'aide de nouvelles données financières.

### Processus

1. **Récupération de la requête utilisateur** :
    - La fonction extrait le nom du fichier contenant les données de la requête utilisateur depuis le payload de la requête déclenchante.
    - Les données de la requête sont récupérées depuis Google Cloud Storage.

2. **Mise à jour des paramètres de la requête** :
    - Le nombre d'exécutions courantes et la fenêtre de dates sont mis à jour en fonction de la configuration initiale et de la fréquence de réexécution.

3. **Envoi de la requête à l'API de backtesting** :
    - Les données mises à jour sont envoyées à l'API de backtesting via une requête POST.

4. **Sauvegarde des résultats et gestion des exécutions** :
    - Les données mises à jour sont sauvegardées de nouveau dans Cloud Storage.
    - Si le nombre maximal d'exécutions est atteint, la tâche planifiée dans Cloud Scheduler est supprimée pour éviter des exécutions supplémentaires.

5. **Publication des résultats sur bucket** :
    - Les résultats du backtesting sont enregistrés dans un bucket "resultats_api" sur google cloud storage.
    - Les résultats peuvent être récupérés par la route '/get_result'.
### Sécurité et Gestion des Erreurs

- La fonction vérifie l'existence du fichier de données dans le payload de la requête déclenchante et gère les erreurs potentielles liées à l'absence de ces données.


### Usage et Avantages

Cette fonction Cloud facilite la réexécution automatique des stratégies de trading sans intervention manuelle, permettant aux utilisateurs de tester l'efficacité de leurs stratégies sur de nouvelles données financières et d'observer l'évolution des performances de leurs stratégies au fil du temps.

```python
import google.cloud.storage
from google.cloud import scheduler_v1
import requests
import json
import os
from flask import escape
import base64
from datetime import datetime, timedelta

def trigger_api(request):
    request_json = request.get_json(silent=True)
    if request_json and 'file_name' in request_json:
        file_name = request_json['file_name']
    else:
        return 'Le nom du fichier est manquant dans la requête', 400
    
    bucket_name = "backtestapi_bucket"
    storage_client = google.cloud.storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    user_request_json = blob.download_as_text()

    # Conversion des données JSON en dictionnaire
    user_request_data = json.loads(user_request_json)

    # Configuration
    api_url = "https://backtestapi.onrender.com/backtesting/"
    project_id = 'boreal-forest-416815'
    location = 'europe-west1'

    # Lecture du nombre maximal d'exécutions depuis le dictionnaire
    max_executions = user_request_data.get("nb_execution", 1)

    # Mise à jour du nombre d'exécutions et vérification de la limite
    current_execution_count = user_request_data.get("current_execution_count", 0) + 1
    user_request_data["current_execution_count"] = current_execution_count

    # Màj de la fenêtre de date 
    dates = user_request_data.get("dates")
    delta = user_request_data.get("repeat_frequency")
    date_fin = datetime.strptime(dates[1], "%Y-%m-%d")
    date_fin = date_fin + timedelta(days=delta)
    dates[1] = date_fin.strftime("%Y-%m-%d")
    user_request_data["dates"] = dates

    # Envoi de la requête POST à l'API FastAPI
    response = requests.post(api_url, json=user_request_data)
    
    # Sauvegarde des données mises à jour dans Cloud Storage
    updated_user_request_json = json.dumps(user_request_data)
    blob.upload_from_string(updated_user_request_json, content_type='application/json')

    # Vérification si le nombre maximum d'exécutions est atteint
    if current_execution_count >= max_executions:
        # Suppression de la tâche Cloud Scheduler
        scheduler_client = scheduler_v1.CloudSchedulerClient()
        job_path = scheduler_client.job_path(project_id, location, file_name)
        scheduler_client.delete_job(name=job_path)
    
    bucket_results_name = 'results_api'
    bucket_results = storage_client.bucket(bucket_results_name)
    request_id = user_request_data.get('request_id')
    results_blob = bucket_results.blob(f'{request_id}.json')
    results_blob.upload_from_string(json.dumps(response.json()), content_type='application/json')


    return f'Results are stored with ID: {request_id}'
```