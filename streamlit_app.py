import requests
import streamlit as st
import pandas as pd

# L'URL de votre endpoint FastAPI (adaptez selon votre configuration)
API_URL = "https://backtestapi.onrender.com/backtesting/"

# Widgets Streamlit pour collecter les entrées de l'utilisateur
func_strat = st.text_area("Entrer votre fonction de trading :", height=300)
requirements = st.text_input("Liste des imports nécessaires, séparés par une virgule :")
tickers = st.text_input("Liste des tickers considérés, séparés par une virgule :")
dates_calibration = st.text_input("Dates de calibration (YYYY-MM-DD,YYYY-MM-DD) :")
interval = st.selectbox("Sélectionnez l'intervalle :", ["1d", "1w", "1m"])
amount = st.text_input("Montant initial du portefeuille :")
rqt_name = st.text_input("Nom de la requête pour identification :")

# Lorsque l'utilisateur appuie sur le bouton 'Exécuter le Backtest'
if st.button('Exécuter le Backtest'):
    # Préparation des données à envoyer
    data_to_send = {
        "func_strat": func_strat,
        "requirements": requirements.split(","),
        "tickers": tickers.split(","),
        "dates_calibration": dates_calibration.split(","),
        "interval": interval,
        "amount": amount,
        "rqt_name": rqt_name
    }

    # Appel à l'API FastAPI
    response = requests.post(API_URL, json=data_to_send)
    if response.status_code == 200:
        results = response.json()
        st.write("Résultats du backtesting :", results)
    else:
        st.write("Erreur lors de l'appel à l'API :", response.text)
