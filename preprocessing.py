from typing import List, Optional
import pandas as pd
import numpy as np
import streamlit as st
from sklearn.preprocessing import (
    MinMaxScaler, StandardScaler, RobustScaler, Normalizer, MaxAbsScaler, OneHotEncoder
)
from scipy import stats
from main import Dashboard


class Preprocessing:
    def __init__(self, data: pd.DataFrame):
        self.data: pd.DataFrame = data
        self.scaler: Optional[str] = None
        self.cleaning_methods: Optional[List[str]] = None

    def run(self) -> Optional[pd.DataFrame]:
        """
        Método principal para executar o fluxo de pré-processamento.

        Returns:
            Optional[pd.DataFrame]: DataFrame pré-processado, ou None se nenhuma ação for realizada.
        """
        self.select_preprocessing_method()
        self.select_cleaning_method()
        if st.sidebar.button('Aplicar'):
            new_data = self.__apply_preprocessing()
            show = st.sidebar.checkbox('Mostrar dados após pré-processamento', value=True)
            if new_data is not None and show:
                self.__show(new_data)
            return new_data
        return None

    def select_cleaning_method(self) -> None:
        """
        Exibe uma caixa de seleção no sidebar para selecionar métodos de limpeza.
        """
        cleaning_method = st.sidebar.multiselect(
            'Selecione um método de limpeza:',
            ('nenhum', 'Remover linhas com valores nulos', 'Remover linhas duplicadas', 'Remover ruídos'),
            default='nenhum'
        )
        self.cleaning_methods = cleaning_method

    def select_preprocessing_method(self) -> None:
        """
        Exibe uma caixa de seleção no sidebar para selecionar método de normalização.
        """
        preprocessing_method = st.sidebar.selectbox(
            'Selecione um método de normalização:',
            ('nenhum', 'MinMaxScaler', 'StandardScaler', 'RobustScaler', 'Normalizer', 'MaxAbsScaler'),
            index=0
        )
        self.scaler = preprocessing_method

    def __apply_preprocessing(self) -> pd.DataFrame:
        """
        Aplica os métodos de limpeza, normalização e pré-processamento aos dados.

        Returns:
            pd.DataFrame: DataFrame após aplicação dos métodos.
        """
        scaler_map = {
            'MinMaxScaler': MinMaxScaler(),
            'StandardScaler': StandardScaler(),
            'RobustScaler': RobustScaler(),
            'Normalizer': Normalizer(),
            'MaxAbsScaler': MaxAbsScaler()
        }

        scaler = scaler_map.get(self.scaler)
        df = self.data.copy()

        # Aplicar limpeza
        if 'nenhum' not in self.cleaning_methods:
            for method in self.cleaning_methods:
                if method == 'Remover linhas com valores nulos':
                    df = self.__clean_null(df)
                elif method == 'Remover linhas duplicadas':
                    df = self.__clean_duplicates(df)
                elif method == 'Remover ruídos':
                    df = self.__clean_noise(df)

        # Separar as colunas numéricas
        numerical_df = df.select_dtypes(exclude=['object'])

        # Aplicar normalização às colunas numéricas
        if self.scaler != 'nenhum' and scaler:
            if not numerical_df.empty:
                for col in numerical_df.columns:
                    scaled_data = scaler.fit_transform(numerical_df[[col]])
                    numerical_df[col] = scaled_data
                    st.write(f"{col} normalizado pelo método {self.scaler}:")
                    st.write(numerical_df[[col]])
            else:
                st.write("Não há colunas numéricas para normalização.")
        else:
            st.write("Nenhum método de normalização selecionado.")

        # Passar os dados normalizados para o processamento categórico
        final_df = self.preprocess_categorical_data(df, numerical_df)

        st.write("Dados após pré-processamento:")
        st.write(final_df)

        return final_df

    def preprocess_categorical_data(self, df: pd.DataFrame, numerical_df: pd.DataFrame) -> pd.DataFrame:
        """
        Método para pré-processar dados categóricos e concatenar com os dados numéricos.

        Args:
            df (pd.DataFrame): DataFrame original contendo colunas categóricas.
            numerical_df (pd.DataFrame): DataFrame com colunas numéricas pré-processadas.

        Returns:
            pd.DataFrame: DataFrame após pré-processamento e concatenação.
        """
        categorical_df = df.select_dtypes(include=['object'])

        if not categorical_df.empty:
            enc = OneHotEncoder(sparse_output=False)  # `sparse_output=False` para retornar um DataFrame
            encoded_data = pd.DataFrame(enc.fit_transform(categorical_df), columns=enc.get_feature_names_out(categorical_df.columns))


            final_df = pd.concat([numerical_df, encoded_data], axis=1)
        else:
            final_df = numerical_df

        return final_df

    def __show(self, new_data: pd.DataFrame) -> None:
        """
        Exibe o DataFrame antes e depois da aplicação dos métodos de limpeza e normalização.

        Args:
            new_data (pd.DataFrame): DataFrame após aplicação dos métodos.
        """
        st.write("Tabela original:")
        st.write(self.data.count())
        st.write("Tabela após pré-processamento:")
        st.write(new_data.count())
        Dashboard().download_spreadsheet(new_data, "preprocessed_data.csv")

    def __clean_null(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove linhas com valores nulos do DataFrame.

        Args:
            df (pd.DataFrame): DataFrame a ser limpo.

        Returns:
            pd.DataFrame: DataFrame sem valores nulos.
        """
        st.write('Valores nulos antes da limpeza:', df.isnull().sum())
        return df.dropna()

    def __clean_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove linhas duplicadas do DataFrame.

        Args:
            df (pd.DataFrame): DataFrame a ser limpo.

        Returns:
            pd.DataFrame: DataFrame sem linhas duplicadas.
        """
        st.write('Valores duplicados antes da limpeza:', df.duplicated().sum())
        return df.drop_duplicates()

    def __clean_noise(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove ruídos dos dados utilizando o método do Z-Score.

        Args:
            df (pd.DataFrame): DataFrame a ser limpo.

        Returns:
            pd.DataFrame: DataFrame sem ruídos.
        """
        categorical_values = df.select_dtypes(include=['object'])
        numerical_df = df.drop(columns=categorical_values.columns.tolist())
        bool_columns = numerical_df.select_dtypes(include=["bool"]).columns.tolist()
        numerical_df[bool_columns] = numerical_df[bool_columns].astype(int)

        st.write('Valores ruidosos antes da limpeza:', (np.abs(stats.zscore(numerical_df)) > 3).sum())
        cleaned_df = numerical_df[(np.abs(stats.zscore(numerical_df)) < 3).all(axis=1)]

        cleaned_df = pd.concat([cleaned_df, categorical_values], axis=1)
        return cleaned_df
