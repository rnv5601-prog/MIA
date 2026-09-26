import streamlit as st
import tempfile
import os
from google import genai
from google.genai import types

# Configuração da página
st.set_page_config(page_title="Gestão de Transporte Hospitalar", page_icon="🚑")

st.title("🚑 Assistente de Transporte Hospitalar")
st.subheader("Agendamentos, Rotas e Análise de Arquivos")

# Campo para Chave de API na barra lateral
with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("Sua API Key do Gemini:", type="password")
    st.info("Obtenha sua chave no Google AI Studio.")

# Campo para o usuário escrever a solicitação
prompt_texto = st.text_area(
    "Digite sua solicitação ou dúvida:",
    placeholder="Ex: Organize a rota dos pacientes das 08h ou peça para analisar o arquivo anexado...",
    height=100
)

# Upload de arquivos (Áudio, Imagem ou Documentos)
arquivo_enviado = st.file_uploader(
    "Anexe um arquivo (Foto da escala, Áudio do WhatsApp, PDF, etc.):",
    type=["png", "jpg", "jpeg", "mp3", "wav", "ogg", "pdf", "csv"]
)

# Botão de Executar
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

                # Se o usuário enviou um arquivo, faz a leitura temporária
                if arquivo_enviado is not None:
                    # Salva temporariamente o arquivo no disco
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{arquivo_enviado.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(arquivo_enviado.getvalue())
                        tmp_path = tmp_file.name

                    # Faz upload para a API Gemini
                    arquivo_api = client.files.upload(
                        file=tmp_path,
                        config=types.UploadFileConfig(mime_type=arquivo_enviado.type)
                    )
                    conteudos.append(arquivo_api)

                if prompt_texto:
                    conteudos.append(prompt_texto)

                # Instruções do sistema focadas na sua necessidade de saúde
                system_instruction = """
                Você é um assistente especialista em logística hospitalar e transporte de pacientes.
                Analise detalhadamente escalas, rotas, áudios e imagens enviadas.
                Sempre responda de forma clara, priorizando urgência, otimização de veículos e organização tabular quando aplicável.
                """

                # Executa a chamada no modelo Gemini
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=conteudos,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2
                    )
                )

                # Exibe o resultado
                st.success("Análise concluída!")
                st.markdown("---")
                st.markdown(response.text)

                # Limpa arquivo temporário
                if arquivo_enviado is not None and os.path.exists(tmp_path):
                    os.remove(tmp_path)

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")
