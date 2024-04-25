import re
from pathlib import Path
import pickle
from unidecode import unidecode
import streamlit as st
from cryptography.fernet import Fernet
import openai

CHAVE_CRIPTOGRAFIA = b'72WM3vHTYph_VyGjix1er6oCWTFZeAKM2u2ccZjAj6s='
CHAVE_API_CRIPTOGRAFADA = b'gAAAAABmEF9yxl_rg21p1-OoNdVHZxqiWoEsrZcLWR7uPqex10ximY5j65emibWHXskvNDVQHqk18VgCUKMeu5Jt-7_27TTTanB3c5OAE2BYdzgiNl5ItFzbnSk0I7ZJAUPEaTJlCBeZF82wl_UE2XN_l-X17PQNRA=='

cipher_suite = Fernet(CHAVE_CRIPTOGRAFIA)

PASTA_CONFIGERACOES = Path(__file__).parent / 'configuracoes'
PASTA_CONFIGERACOES.mkdir(exist_ok=True)
PASTA_MENSAGENS = Path(__file__).parent / 'mensagens'
PASTA_MENSAGENS.mkdir(exist_ok=True)
CACHE_DESCONVERTE = {}

def decodifica_chave_api():
    chave_api_decodificada = cipher_suite.decrypt(CHAVE_API_CRIPTOGRAFADA).decode()
    return chave_api_decodificada

def retorna_resposta_modelo(mensagens, modelo='gpt-4-turbo-preview', temperatura=0):
    openai.api_key = decodifica_chave_api() 
    chat_messages = [{"role": m['role'], "content": m['content']} for m in mensagens]

    response = openai.ChatCompletion.create(
        model=modelo,
        messages=chat_messages,
        temperature=temperatura
    )

    if response.choices and len(response.choices) > 0:
        return response.choices[0].message['content']
    else:
        return "Desculpe, não consegui processar sua resposta."

def converte_nome_mensagem(nome_mensagem):
    nome_arquivo = unidecode(nome_mensagem)
    nome_arquivo = re.sub(r'\W+', '', nome_arquivo).lower()
    return nome_arquivo

def desconverte_nome_mensagem(nome_arquivo):
    if not nome_arquivo in CACHE_DESCONVERTE:
        nome_mensagem = ler_mensagem_por_nome_arquivo(nome_arquivo, key='nome_mensagem')
        CACHE_DESCONVERTE[nome_arquivo] = nome_mensagem
    return CACHE_DESCONVERTE[nome_arquivo]

def retorna_nome_da_mensagem(mensagens):
    for mensagem in mensagens:
        if mensagem.get('type', 'text') == 'text':
            return mensagem['content'][:30] 
    return "Nova Conversa"  

def salvar_mensagens(mensagens):
    if not mensagens:
        return False
    nome_mensagem = retorna_nome_da_mensagem([m for m in mensagens if m.get('type', 'text') == 'text'])
    nome_arquivo = converte_nome_mensagem(nome_mensagem)
    arquivo_salvar = {'nome_mensagem': nome_mensagem, 'nome_arquivo': nome_arquivo, 'mensagem': mensagens}
    with open(PASTA_MENSAGENS / f"{nome_arquivo}.pkl", 'wb') as f:
        pickle.dump(arquivo_salvar, f)

def ler_mensagem_por_nome_arquivo(nome_arquivo, key='mensagem'):
    arquivo_completo = f"{nome_arquivo}.pkl" 
    with open(PASTA_MENSAGENS / arquivo_completo, 'rb') as f:
        mensagens = pickle.load(f)
    return mensagens[key]

def ler_mensagens(mensagens, key='mensagem'):
    if len(mensagens) == 0:
        return []
    nome_mensagem = retorna_nome_da_mensagem(mensagens)
    nome_arquivo = converte_nome_mensagem(nome_mensagem)
    with open(PASTA_MENSAGENS / nome_arquivo, 'rb') as f:
        mensagens = pickle.load(f)
    return mensagens[key]

def listar_conversas():
    conversas = list(PASTA_MENSAGENS.glob('*'))
    conversas = sorted(conversas, key=lambda item: item.stat().st_mtime_ns, reverse=True)
    return [c.stem for c in conversas]

def inicializacao():
    if 'mensagens' not in st.session_state:
        st.session_state['mensagens'] = []
    if 'conversa_atual' not in st.session_state:
        st.session_state['conversa_atual'] = ''
    if 'modelo' not in st.session_state:
        st.session_state['modelo'] = 'gpt-3.5-turbo'
    
def retorna_imagem_modelo(prompt,modelo='dall-e-3'):
    openai.api_key = decodifica_chave_api()
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="512x512"
    )

    if response.data and len(response.data) > 0:
        return response.data[0].url
    else:
        return "Desculpe, não consegui gerar a imagem."

def processar_mensagem(prompt, acao):
    mensagens = st.session_state['mensagens']
    
    nova_mensagem_usuario = {'role': 'user', 'type': 'text', 'content': prompt}
    mensagens.append(nova_mensagem_usuario)

    expressoes_criador = ["quem é seu criador", "quem te criou", "quem criou você", "quem é o seu criador"]

    if any(expressao in prompt.lower() for expressao in expressoes_criador):
        resposta_criador = "O meu criador foi o  Davi Valerio."
        mensagens.append({'role': 'assistant', 'type': 'text', 'content': resposta_criador})
    elif acao == "Enviar mensagem":
        resposta_completa = retorna_resposta_modelo(mensagens, modelo=st.session_state['modelo'])
        mensagens.append({'role': 'assistant', 'type': 'text', 'content': resposta_completa})
    elif acao == "Gerar imagem":
        url_imagem = retorna_imagem_modelo(prompt)
        if url_imagem.startswith("http"):
            mensagens.append({'role': 'assistant', 'type': 'image', 'content': url_imagem})
        else:
            st.error(url_imagem)

    st.session_state['prompt_input'] = ''
    st.session_state['mensagens'] = mensagens
    salvar_mensagens(mensagens)


def apagar_conversa(nome_arquivo):
    """
    Apaga o arquivo de conversa especificado.
    """
    try:
        arquivo_completo = PASTA_MENSAGENS / f"{nome_arquivo}.pkl"
        arquivo_completo.unlink()
        st.success(f"Conversa '{nome_arquivo}' apagada com sucesso.")
    except FileNotFoundError:
        st.error("Arquivo não encontrado.")
    except Exception as e:
        st.error(f"Erro ao apagar a conversa: {e}")

def pagina_principal():
    
    st.markdown("""
    <h1 style='text-align: left; margin-bottom: 20px;'>Chat GP<span style='color: #10B0A0; font-size: 60px;'>TOP</span></h1>
    """, unsafe_allow_html=True)
    
    with st.container():
        for mensagem in st.session_state['mensagens']:
            tipo_mensagem = mensagem.get('type', 'text')

            if tipo_mensagem == 'text':
                chat = st.chat_message(mensagem['role'])
                chat.markdown(mensagem['content'])
            elif tipo_mensagem == 'image':
                st.image(mensagem['content'], caption='Imagem gerada')

    with st.container():
        acao = st.radio("Escolha uma ação:", ("Enviar mensagem", "Gerar imagem"), key='acao')

        prompt = st.text_input('Fale com o chat ou digite um prompt para imagem', value='', key='prompt_input')

        st.button('Enviar', on_click=processar_mensagem, args=(st.session_state['prompt_input'], st.session_state['acao']))
        
def melhora_legibilidade_nome(nome_arquivo):
    nome_melhorado = re.sub(r"(\d+)", r" \1", nome_arquivo)
    nome_melhorado = re.sub(r"(?<=.)([A-Z])", r" \1", nome_melhorado)
    nome_melhorado = nome_melhorado.title()
    
    return nome_melhorado

def tab_conversas(tab):
    tab.button('➕ Nova conversa',
               on_click=seleciona_conversa,
               args=('',),
               use_container_width=True,
               key='nova_conversa_button') 
    tab.markdown('')

    conversas = listar_conversas()
    for indice, nome_arquivo in enumerate(conversas):
        nome_mensagem = desconverte_nome_mensagem(nome_arquivo).capitalize()
        if len(nome_mensagem) == 30:
            nome_mensagem += '...'
        tab.button(nome_mensagem,
                   on_click=seleciona_conversa,
                   args=(nome_arquivo,),
                   disabled=nome_arquivo == st.session_state['conversa_atual'],
                   use_container_width=True,
                   key=f'conversa_{indice}_{nome_arquivo}') 

    with tab.container():
        conversas = listar_conversas()

        conversas_melhoradas = [melhora_legibilidade_nome(nome) for nome in conversas]
        
        conversa_para_apagar = tab.selectbox("Selecione a conversa para apagar:", [""] + conversas_melhoradas, key="conversa_para_apagar")

        indice_selecionado = conversas_melhoradas.index(conversa_para_apagar) if conversa_para_apagar in conversas_melhoradas else -1
        if indice_selecionado != -1:
            nome_arquivo_original = conversas[indice_selecionado]

        if tab.button("Apagar Conversa Selecionada"):
            if conversa_para_apagar:
                apagar_conversa(nome_arquivo_original)
                st.experimental_rerun()
            else:
                tab.warning("Por favor, selecione uma conversa para apagar.")

def seleciona_conversa(nome_arquivo):
    if nome_arquivo == '':
        st.session_state['mensagens'] = []
    else:
        mensagem = ler_mensagem_por_nome_arquivo(nome_arquivo)
        st.session_state['mensagens'] = mensagem
    st.session_state['conversa_atual'] = nome_arquivo

def tab_configuracoes(tab):
    modelo_escolhido = tab.selectbox('Selecione o modelo',
                                     [ 'gpt-4-turbo-preview','gpt-3.5-turbo'])
    st.session_state['modelo'] = modelo_escolhido

def main():
    inicializacao()
    pagina_principal()
    tab1, tab2 = st.sidebar.tabs(['Conversas', 'Configurações'])
    tab_conversas(tab1)
    tab_configuracoes(tab2)

if __name__ == '__main__':
    main()