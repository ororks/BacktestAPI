
from datetime import datetime, timedelta
from google.cloud import scheduler
from google.oauth2 import service_account
from google.cloud import storage
from google.api_core.exceptions import GoogleAPICallError, AlreadyExists
import os
import json

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.relpath("boreal-forest-416815-c57cb5c11bdc.json", start=os.path.curdir)

class CloudScheduler:
    """
    La classe CloudScheduler permet de planifier et de gérer l'exécution automatisée
    de requêtes utilisateur dans le Cloud. Elle utilise Google Cloud Scheduler pour
    configurer des tâches planifiées qui déclenchent des fonctions Cloud, permettant
    ainsi l'exécution récurrente des requêtes de backtesting de stratégies de trading à des intervalles prédéfinis.
    """
    def __init__(self,
                 user_input):
        self.user_input = user_input


    def frequency_to_cron(self):
        """
        Description : Convertit la fréquence de réexécution spécifiée par l'utilisateur en une expression cron
                    compatible avec Google Cloud Scheduler.
        Renvoie : Une chaîne de caractères représentant l'expression cron correspondant à la
                fréquence de réexécution souhaitée.
        """
        if self.user_input.repeat_frequency == 1:
            return "0 0 * * *"  # À minuit chaque jour
        elif self.user_input.repeat_frequency == 7:
            return "0 0 * * 1"  # À minuit tous les lundis
        elif self.user_input.repeat_frequency == 30:
            return "0 0 1 * *"  # À minuit le premier jour de chaque mois
        else:
            raise ValueError("La fréquence spécifiée n'est pas supportée en format cron")

    def save_request_to_storage(self, bucket_name="backtestapi_bucket"):
        """
        Description : Sauvegarde la requête de l'utilisateur dans un fichier JSON sur Google Cloud Storage pour
                    une utilisation ultérieure par la fonction Cloud déclenchée.

        Paramètres :
            bucket_name : Nom du bucket Cloud Storage où le fichier JSON sera sauvegardé.

        Processus :
            Convertit les données de requête utilisateur en JSON.
            Utilise le client Cloud Storage pour créer ou mettre à jour un objet blob contenant
            les données de la requête dans le bucket spécifié.
        """
        try:
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
            file_name = self.user_input.request_id
            blob = bucket.blob(file_name)

            # Télécharge les données dans le blob
            blob.upload_from_string(data_to_save, content_type="application/json")

            print(f"Les données ont été sauvegardées dans {file_name} dans le bucket {bucket_name}.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données dans Cloud Storage: {e}")

    def create_scheduler_job(self, bucket_name="backtestapi_bucket"):
        """
        Description : Crée une tâche planifiée dans Google Cloud Scheduler pour exécuter la requête utilisateur à
        l'heure et à la fréquence spécifiées.

        Paramètres :
            bucket_name : Nom du bucket Cloud Storage où les données de la requête utilisateur sont stockées.

        Processus :
            Construit une requête pour créer une nouvelle tâche dans Google Cloud Scheduler, incluant l'URL
            de la fonction Cloud à déclencher, l'expression cron pour la planification, et les données de la requête
            .
            Utilise le client Cloud Scheduler pour soumettre la requête de création de tâche.
        """
        credentials_path = os.path.relpath("boreal-forest-416815-c57cb5c11bdc.json", start=os.path.curdir)
        credentials = service_account.Credentials.from_service_account_file(credentials_path)

        project = 'boreal-forest-416815'
        location = 'europe-west1'
        parent = f'projects/{project}/locations/{location}'
        job_name = f'{self.user_input.request_id}'
        frequency = self.frequency_to_cron()

        client = scheduler.CloudSchedulerClient(credentials=credentials)
        function_url = "https://europe-west9-boreal-forest-416815.cloudfunctions.net/trigger_api"

        body = json.dumps({"bucket_name": bucket_name, "file_name": self.user_input.request_id}).encode('utf-8')

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

