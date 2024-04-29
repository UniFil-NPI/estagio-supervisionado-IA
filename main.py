# streamlit
import streamlit as st
# Pandas
import pandas as pd
# Matplotlib
import matplotlib.pyplot as plt
# Custom modules
from preprocessing import Preprocessing
from description import Description
# Typing
from typing import List
from typing import Optional

"""
This module provides a Dashboard class for data preprocessing and visualization.
"""

class Dashboard():
    """
    A class for data preprocessing and visualization.
    """

    def __init__(self):
        self.data = pd.read_csv('novo_arquivo.csv', low_memory=False)
        self.preprocessor = Preprocessing(self.data)
        self.description = Description(self.data)

    def run(self) -> None:
        """
        Run the dashboard.
        """
        st.sidebar.title("Pré-processamento de dados")
        selected_option = st.sidebar.radio(
            "Selecione uma opção",
            ["Pré-processamento", "Descrição", "Gráfico sem pré-processamento"]
        )

        if selected_option == "Pré-processamento":
            self.preprocessor._select_preprocessing_method()

        elif selected_option == "Descrição":
            self.description.run()

        elif selected_option == "Gráfico sem pré-processamento":
            self.__generate_graph()

    def __generate_graph(self) -> None:
        """
        Generate a graph without preprocessing.
        """
        st.sidebar.write("Gráfico sem pré-processamento")
        columns = Preprocessing._select_columns()
        if columns:
            cleaned_data = self.preprocessor._clean_data(self.data, columns)
            self.__plot_graph(cleaned_data, columns)

    def __plot_graph(self, data, columns: Optional[List[str]] = None) -> None:
        """
        Plot a graph.
        """
        if columns is None:
            columns = ['situacao']
        for col in columns:
            fig, ax = plt.subplots(figsize=(8, 6))
            col_data = data[col]
            counts = col_data.value_counts()

            counts.plot(kind='bar', ax=ax)

            ax.set_xlabel(col)
            ax.set_ylabel('Quantidade')
            ax.set_title(f'Quantidade de {col}')

            for i, value in enumerate(counts):
                ax.text(i, value + 0.1, str(value), ha='center')

            st.pyplot(fig)

if __name__ == '__main__':
    dashboard = Dashboard()
    dashboard.run()