import streamlit as st
import tempfile
import os
import time
from google import genai
from google.genai import types

st.set_page_config(page_title="Gestão de Transporte Hospitalar", page_icon="🚑")

st.title("🚑 Assistente de Transporte Hospitalar")
st.subheader("Agendamentos, Rotas e Análise de Arquivos")

with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("Sua API Key do Gemini:", type="password")
    st.info("Obtenha sua chave no Google AI Studio.")

prompt_texto = st.text_area(
    "Digite sua solicitação ou dúvida:",
    placeholder="Ex: Organize a rota dos pacientes das 08h ou peça para analisar o arquivo anexado...",
    height=100
)

arquivo_enviado = st.file_uploader(
    "Anexe um arquivo (Foto da escala, Áudio do WhatsApp, PDF, etc.):",
    type=["png", "jpg", "jpeg", "mp3", "wav", "ogg", "pdf", "csv"]
)

if st.button("Processar Solicitação", type="primary"):
    if not api_key:
        st.error("Por favor, insira sua API Key na barra lateral!")
    elif not prompt_texto and not arquivo_enviado:
        st.warning("Insira uma instrução em texto ou anexe um arquivo para prosseguir.")
    else:
        with st.spinner("A IA está analisando sua solicitação..."):
            try:
                client = genai.Client(api_key=api_key)
                conteudos = []

                if arquivo_enviado is not None:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{arquivo_enviado.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(arquivo_enviado.getvalue())
                        tmp_path = tmp_file.name

                    arquivo_api = client.files.upload(
                        file=tmp_path,
                        config=types.UploadFileConfig(mime_type=arquivo_enviado.type)
                    )
                    conteudos.append(arquivo_api)

                if prompt_texto:
                    conteudos.append(prompt_texto)

                system_instruction = """
                Você é um assistente especialista em logística hospitalar e transporte de pacientes.
                Analise detalhadamente escalas, rotas, áudios e imagens enviadas.
                Sempre responda de forma clara, priorizando urgência, otimização de veículos e organização tabular quando aplicável.
                """

                # Tentativa com retry em caso de instabilidade (503)
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=conteudos,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.2
                            )
                        )
                        break
                    except Exception as e:
                        if "503" in str(e) and attempt < max_retries - 1:
                            time.sleep(2)  # Aguarda 2 segundos antes de tentar novamente
                            continue
                        else:
                            raise e

                st.success("Análise concluída!")
                st.markdown("---")
                st.markdown(response.text)

                if arquivo_enviado is not None and os.path.exists(tmp_path):
                    os.remove(tmp_path)

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")
