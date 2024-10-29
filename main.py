import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional
from models import TBPrimaryActions
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from report import ReportsDashboard
from file_viewer import FileViewer

from streamlit_option_menu import option_menu
#from drive_upload import GoogleDriveUploader
import streamlit_antd_components as sac
import extra_streamlit_components as stx

engine = create_engine('sqlite:///actions.db')
Session = sessionmaker(bind=engine)
session = Session()

st.markdown(
    """
    <style>
    [data-testid="stMarkdownContainer"] p {
        font-size: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

class Dashboard:
    """
    A class for data preprocessing and visualization.
    """

    def __init__(self) -> None:
        self.data: pd.DataFrame = st.session_state.get('data', pd.DataFrame())
        self.processed_data: pd.DataFrame = st.session_state.get('processed_data', None)
        self.dataset_name: str = st.session_state.get('dataset_name', 'Desconhecido')
        from preprocessing import Preprocessing 
        self.preprocessor: Preprocessing = Preprocessing(self.data)
        from description import Description 
        self.description: Description = Description(self.data)
        from aiprocessing import AiProcessing 
        self.aiprocessing: AiProcessing = AiProcessing(self.data,self.processed_data)
        if 'action_saved' not in st.session_state:
            st.session_state['action_saved'] = False

    def run(self) -> None:
        """
        Run the dashboard.
        """

        image_url = "https://a10br.com/wp-content/uploads/2022/08/Imagens-site-A10_Integrada.png"

        with st.sidebar:
            # Exibir a imagem na barra lateral
            st.image(image_url, width=285)

            # Menu lateral
            selected_option = option_menu(
                "",  # Deixa o título vazio, já que a imagem está no topo
                ["Upload de arquivo", "Pré-processamento","Processamento com IA", "Visualizar Arquivos",  "Análise sem pré-processamento", "Descrição",  "Mesclar Bases", "Relatórios"], 
                icons=[ 'file-earmark-arrow-up','gear','clipboard-data', 'search' , 'sliders', 'card-text', 'union', 'clipboard-pulse'], 
                menu_icon="tree", 
                default_index=0,
            )

        # Dicionário de opções com suas respectivas funções
        options: dict[str, callable] = {
            "Pré-processamento": self.preprocessor.run,
            "Análise sem pré-processamento": self.__generate_graph,
            "Descrição": self.description.run,
            "Processamento com IA": self.__process_with_ai,
            "Upload de arquivo": self.__upload_file,
            "Mesclar Bases": self.__merge_spreadsheets,
            "Relatórios": ReportsDashboard().run,
            "Visualizar Arquivos": FileViewer().visualizar_arquivos,
            #"Upload do Drive": GoogleDriveUploader(self).display
        }

        # Executar a função correspondente ao item selecionado
        if selected_option in options:
            result = options[selected_option]()
        
        # Verificar a última opção e salvar a ação
        last_option = st.session_state.get('last_option', None)
        if selected_option != last_option:
            if selected_option in ["Pré-processamento", "Processamento com IA"]:
                is_ai = (selected_option == "Processamento com IA")
                self.__save_primary_action(selected_option, is_ai)
            st.session_state['last_option'] = selected_option

        # Processamento com IA
        if selected_option == "Processamento com IA":
          
            processed_data, method = result
            if method == 'Regressão':
                st.write("aguarde, realizando a regressão")
                self.aiprocessing.regression()
            elif method == 'Classificação':
                self.aiprocessing.classification()

        # Gerenciar chaves únicas para widgets selectbox ou similares
        # if selected_option == "Pré-processamento":
        #     st.selectbox('Escolha uma opção de pré-processamento:', options=['Opção 1', 'Opção 2'], key='preprocessing_selectbox')

        # elif selected_option == "Processamento com IA":
        #     st.selectbox('Escolha o método de IA:', options=['Regressão', 'Classificação'], key='ia_selectbox')

    def __save_primary_action(self, action_name: str, is_ai: bool) -> None:
        """
        Save the primary action to the database.
        """
        try:
            dataset_name = st.session_state['dataset_name']

            new_action = TBPrimaryActions(
                action_name=action_name,
                dataset_name=dataset_name,
                is_ai=is_ai
            )
            session.add(new_action)
            session.commit()
            session.close()
            st.write(f"Ação '{action_name}' salva com sucesso!")
        except Exception as e:
            print(f"Erro ao salvar a ação: {e}")
        
    def __process_with_ai(self):
        """
        Processa os dados com IA, mostrando a interface adequada com base no tipo selecionado.
        """
        self.aiprocessing.remove_coluna()

        # Recupera o dado processado e o método (Classificação ou Regressão)
        processed_data, method = self.aiprocessing.run()
        st.session_state['processed_data'] = processed_data
        st.session_state['method'] = method

       

        return processed_data, method

    def __upload_file(self) -> None:
        """
        Upload a file.
        """
        st.title("Upload de arquivo")
        st.write("Escolha o tipo de upload")

        # Componente de escolha de upload
        upload_option = sac.segmented(
            items=[
                sac.SegmentedItem(label='Upload', icon='file-earmark-arrow-up'),
                sac.SegmentedItem(label='Upload do Drive', icon='cloud-arrow-up')
            ], align='left', size='lg'
        )

        # Lógica para upload de arquivos
        if upload_option == 'Upload':
            st.subheader('Insira um arquivo .csv')
            file: Optional[st.uploaded_file_manager.UploadedFile] = st.file_uploader("Insira um arquivo .CSV a partir do seu dispositivo", type="csv")

            if file is not None:
                try:
                    data = pd.read_csv(file)
                    self.save_df(data, file.name)
                except Exception as e:
                    st.error(f"Erro ao carregar o arquivo: {e}")

        elif upload_option == 'Upload do Drive':
            # Executa a funcionalidade para upload do Google Drive
            #GoogleDriveUploader(self).display()
            print("google")

    def save_df(self, data: pd.DataFrame, df_name) -> None:
        if isinstance(data, pd.DataFrame):
            st.session_state.data = data 
            st.session_state['dataset_name'] = df_name
            st.write("Arquivo CSV carregado com sucesso!")

    @staticmethod
    @st.cache_data
    def convert_df(_df: pd.DataFrame) -> bytes:
        return _df.to_csv(index=False).encode('utf-8')
    
    def download_spreadsheet(self, df: pd.DataFrame, filename: str) -> None:
        """
        Download a spreadsheet.
        """
        try:
            
            csv: bytes = self.convert_df(df)
            st.download_button(
                label="Baixar base",
                data=csv,
                file_name=filename,
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Erro ao baixar a base: {e}")

    def __merge_spreadsheets(self) -> None:
        """
        Merge two spreadsheets based on user-selected keys, remove values above 50000
        from selected columns, and remove duplicated columns.
        """
        st.subheader("Carregar base 1:")
        file1: Optional[st.uploaded_file_manager.UploadedFile] = st.file_uploader("Upload base 1", type="csv", key="file1")

        st.subheader("Carregar base 2:")
        file2: Optional[st.uploaded_file_manager.UploadedFile] = st.file_uploader("Upload base 2", type="csv", key="file2")

        if file1 is not None and file2 is not None:
            try:
                data1: pd.DataFrame = pd.read_csv(file1)
                data2: pd.DataFrame = pd.read_csv(file2)

                # Selecionar as chaves de junção para cada base
                st.subheader("Selecionar chave de junção para cada base:")
                key_column1: str = st.selectbox("Selecionar chave de junção para base 1", data1.columns)
                key_column2: str = st.selectbox("Selecionar chave de junção para base 2", data2.columns)

                if st.button("Mesclar Bases"):
                    # Remover valores maiores que 50000 das chaves selecionadas
                    st.write(f"Removendo valores maiores que 50000 da coluna '{key_column1}' na base 1...")
                    data1 = data1[data1[key_column1] <= 50000]
                    st.write(f"base 1 filtrada: {len(data1)} registros restantes.")

                    st.write(f"Removendo valores maiores que 50000 da coluna '{key_column2}' na base 2...")
                    data2 = data2[data2[key_column2] <= 50000]
                    st.write(f"base 2 filtrada: {len(data2)} registros restantes.")

                    # Realizar a junção dos dados
                    st.write("Mesclando as duas bases...")
                    merged_data: pd.DataFrame = pd.merge(
                        data1,
                        data2,
                        left_on=key_column1,
                        right_on=key_column2,
                        how='inner'  # Realizando junção interna para remover linhas sem correspondência
                    )
                    st.write(f"Bases mescladas com sucesso! {len(merged_data)} registros resultantes.")
                    st.write(merged_data.head())

                    # Remover colunas duplicadas
                    st.write("Removendo colunas duplicadas...")
                    duplicated_columns = merged_data.columns[merged_data.T.duplicated()]
                    merged_data = merged_data.loc[:, ~merged_data.T.duplicated()]
                    st.write(f"\nColunas duplicadas removidas: {list(duplicated_columns)}")
                    st.write(f"Dimensões finais após remover colunas duplicadas: {merged_data.shape}")

                    # Exibir os dados resultantes
                    st.write("Dados finais após junção e remoção de duplicatas:")
                    st.write(merged_data.head())

                    # Baixar o resultado final
                    if not merged_data.empty:
                        self.download_spreadsheet(merged_data, "classif_prod_merged.csv")
                    else:
                        st.write("O DataFrame está vazio. Nenhum arquivo CSV será gerado.")
            
            except Exception as e:
                st.error(f"Erro ao processar as base: {e}")


    def __generate_graph(self) -> None:
        """
        Generate a graph without preprocessing.
        """
        st.title("Análise sem pré-processamento")
        st.write("Escolha as colunas para fazer a análise sem pré-processamento")
        columns: List[str] = self.description._select_columns()

        with st.expander(f"Informações sobre das colunas"):
            st.write(f"Infos da coluna {columns}")
            self.__plot_graph(self.data, columns)

    def __plot_graph(self, not_cleaned_data: pd.DataFrame, columns: Optional[List[str]] = None) -> None:
        """
        Plot a graph.
        """
        numeric_columns: pd.Index = not_cleaned_data.select_dtypes(include=np.number).columns
        selected_numeric_columns: List[str] = [col for col in numeric_columns if col in columns]
        non_numeric_columns: List[str] = [col for col in columns if col not in selected_numeric_columns]
        if selected_numeric_columns:
            for col in selected_numeric_columns:
                st.write(not_cleaned_data[col].describe())
        if non_numeric_columns:
            for col in non_numeric_columns:
                fig_width: float = 20 / len(columns)
                fig, ax = plt.subplots(figsize=(fig_width, 6))

                col_data: pd.Series = not_cleaned_data[col]
                counts: pd.Series = col_data.value_counts()

                counts.plot(kind='bar', ax=ax)

                ax.set_xlabel(col)
                ax.set_ylabel('Quantidade')
                ax.set_title(f'Quantidade de {col}')

                for i, v in enumerate(counts.values):
                    ax.text(i, v + 0.1, str(v), ha='center')

                st.pyplot(fig)

if __name__ == '__main__':
    dashboard = Dashboard()
    #uploader = GoogleDriveUploader(dashboard)  
    dashboard.run()
