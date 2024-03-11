import os
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


def generate_fake_data(start_date, end_date):
    date_range = pd.date_range(start=start_date, end=end_date)
    data = np.random.randn(len(date_range), 2)
    df = pd.DataFrame(data, columns=['Value1', 'Value2'], index=date_range)
    return df


def plot_data(df):
    st.subheader('Graphique des données')
    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df['Value1'], label='Value1')
    plt.plot(df.index, df['Value2'], label='Value2')
    plt.xlabel('Date')
    plt.ylabel('Valeur')
    plt.title('Données Value1 et Value2')
    plt.legend()
    st.pyplot()


def main():
    st.title('Analyse des indicateurs financiers')

    # Sélection des dates de début et de fin
    start_date = st.date_input('Date de début', value=pd.to_datetime('2020-01-01'))
    end_date = st.date_input('Date de fin', value=pd.to_datetime('2021-01-01'))

    # Affichage des indicateurs
    data_path = os.path.abspath("stats_backtest.json")
    with open(data_path) as json_file:
        stats_dict = json.load(json_file)

    for indicator, value in stats_dict.items():
        st.write(f"**{indicator}:** {value}")

    # Affichage des graphiques si les données sont disponibles
    if st.checkbox('Afficher les graphiques'):
        df = generate_fake_data(start_date, end_date)
        plot_data(df)


if __name__ == "__main__":
    main()
