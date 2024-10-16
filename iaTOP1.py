import re
from pathlib import Path
import pickle
from unidecode import unidecode
import streamlit as st
from cryptography.fernet import Fernet
import openai

CHAVE_CRIPTOGRAFIA = b'AZCjUmHaKQAijnRsvHkaRmwQaxQAO-ohT-jLQqEU5G4='
CHAVE_API_CRIPTOGRAFADA = b'gAAAAABnBtw7kpP2-kRxrE5ia8E9EdpY8mnO4Z8kZsU808DRfdTnTOKqBfZ4hudKzh6D5HRczpCj2mJp-P7qi5ZyHYeGkepL18DOwWAW3ikPeRMqf5PPwieTE4wNVUxEO0-6owifYcbeTdS-LFy4RSQUJG2NAF2h1jNqpyu0iQO2bMfd7XCezjV09FAoLxBjdzsHQwK2O0EHvaM1zaWDEFxibCTtUcFXhG1UNwnrHAFvwA9ztURRT4_Ng0HVDyegkcIOqBHYCPodZ71Z5hBu3t_W1XglNa7aM_s07lRqPqJJJOwebjwFTZM='

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

PALAVRAS_CHAVE_ENGENHARIA_MATEMATICA = [
    'estrutura', 'estruturas', 'concreto', 'concretos', 'ponte', 'pontes', 'engenharia civil', 'edificação', 'edificações', 'cálculo', 'cálculos', 'resistência', 'resistências', 
    'física', 'físicas', 'material de construção', 'materiais de construção', 'hidráulica', 'hidráulicas', 'solo', 'solos', 'fundação', 'fundações', 'matemática', 'álgebra',
    'geometria', 'geometrias', 'trigonometria', 'trigonometrias', 'cálculo diferencial', 'cálculo integral', 'integral', 'integrais', 'engenharia estrutural', 'viga', 'vigas',
    'diferencial', 'diferenciais', 'mecânica', 'mecânicas', 'tensão', 'tensões', 'carga', 'cargas', 'torre', 'torres', 'dimensionamento', 'dimensionamentos', 'fator de segurança', 'fatores de segurança',
    'engenharia geotécnica', 'topografia', 'topografias', 'pavimentação', 'pavimentações', 'drenagem', 'drenagens', 'infraestrutura', 'infraestruturas', 'túnel', 'túneis', 
    'viaduto', 'viadutos', 'sistema estrutural', 'sistemas estruturais', 'engenharia de transportes', 'geologia aplicada', 'carga estrutural', 'cargas estruturais', 
    'norma técnica', 'normas técnicas', 'projeto estrutural', 'projetos estruturais', 'muro de arrimo', 'muros de arrimo', 'patologia das construções', 'patologias das construções', 
    'segurança estrutural', 'seguranças estruturais', 'cimento', 'argamassa', 'concreto armado', 'concretos armados', 'concreto protendido', 'concretos protendidos', 
    'estrutura metálica', 'estruturas metálicas', 'alvenaria estrutural', 'alvenarias estruturais', 'ponte suspensa', 'pontes suspensas', 'engenharia hidráulica', 'sistema de abastecimento', 'sistemas de abastecimento',
    'saneamento', 'saneamentos', 'tratamento de água', 'tratamentos de água', 'esgoto', 'esgotos', 'irrigação', 'irrigações', 'barragem', 'barragens',
    'engenharia ambiental', 'sustentabilidade', 'sustentabilidades', 'construção civil', 'construções civis', 'cantilever', 'método dos elementos finitos', 'engenharia de tráfego',
    'conforto térmico', 'confortos térmicos', 'acústica', 'acústicas', 'engenharia de custos', 'gestão de projeto', 'gestões de projetos', 'cronograma de obra', 'cronogramas de obras', 'análise estrutural', 'análises estruturais',
    'cálculo de viga', 'cálculos de vigas', 'cálculo de pilares', 'engenharia de materiais', 'desempenho estrutural', 'norma de segurança', 'normas de segurança', 'tensão admissível', 'tensões admissíveis',
    'dimensionamento de fundação', 'dimensionamentos de fundações', 'movimentação de terra', 'movimentações de terra', 'maquinário de construção', 'maquinários de construção', 'projeto de edificação', 'projetos de edificações',
    'matemática', 'álgebra', 'geometria', 'geometrias', 'trigonometria', 'trigonometrias', 'cálculo diferencial', 'cálculo integral', 'limite', 'limites', 'função', 'funções',
    'equação diferencial', 'equações diferenciais', 'série de taylor', 'séries de taylor', 'número complexo', 'números complexos', 'análise matemática', 'matriz', 'matrizes', 'determinante', 'determinantes',
    'sistema linear', 'sistemas lineares', 'vetor', 'vetores', 'geometria analítica', 'probabilidade', 'probabilidades', 'estatística', 'estatísticas', 'combinatória', 'combinatórias', 'progressão aritmética', 'progressões aritméticas',
    'progressão geométrica', 'progressões geométricas', 'teoria dos números', 'matemática financeira', 'logaritmo', 'logaritmos', 'exponencial', 'exponenciais', 'raiz', 'raízes', 'fração', 'frações',
    'tangente', 'tangentes', 'derivada', 'derivadas', 'integração por partes', 'equação algébrica', 'equações algébricas', 'polinômio', 'polinômios', 'transformada de laplace',
    'geometria espacial', 'teorema de pitágoras', 'teoremas de pitágoras', 'teorema de trigonometria', 'teoremas de trigonometria', 'área', 'áreas', 'volume', 'volumes', 'comprimento de arco', 'comprimentos de arco',
    'circunferência', 'circunferências', 'raio', 'raios', 'diâmetro', 'diâmetros', 'seno', 'senos', 'cosseno', 'cossenos', 'cotangente', 'cotangentes', 'secante', 'secantes', 'co-secante', 'co-secantes',
    'fatoração', 'fatoraçãos', 'número primo', 'números primos', 'teorema fundamental da álgebra', 'regressão linear', 'regressões lineares', 'análise de dados', 'medida de tendência central', 'medidas de tendência central',
    'média', 'médias', 'mediana', 'moda', 'variância', 'variâncias', 'desvio padrão', 'desvios padrões', 'distribuição normal', 'distribuições normais', 'distribuição binomial', 'distribuições binomiais', 'hipótese estatística', 'hipóteses estatísticas',
    'equação de segundo grau', 'equações de segundo grau', 'equação paramétrica', 'equações paramétricas', 'ponto crítico', 'pontos críticos', 'intervalo de confiança', 'intervalos de confiança', 'correlação', 'correlações',
    'análise combinatória', 'análises combinatórias', 'binômio de newton', 'limite lateral', 'função logarítmica', 'funções logarítmicas', 'função exponencial', 'funções exponenciais', 'cálculo numérico', 'probabilidade condicional',
    'geotecnia', 'construção sustentável', 'edifício inteligente', 'edifícios inteligentes', 'engenharia urbana', 'sistema de transporte público', 'sistemas de transporte público', 'mobilidade urbana', 'eficiência energética', 'eficiências energéticas',
    'isolamento térmico', 'isolamentos térmicos', 'avaliação de impacto ambiental', 'avaliações de impacto ambiental', 'licenciamento ambiental', 'perícia de obra', 'perícias de obras', 'terraplenagem', 'tecnologia do concreto',
    'estabilidade de taludes', 'controle de erosão', 'qualidade da água', 'planejamento urbano', 'infraestrutura verde', 'gestão de resíduos', 'reaproveitamento de material', 'reaproveitamento de materiais', 'reciclagem de concreto', 'avaliação estrutural',
    'ponte de concreto', 'pontes de concreto', 'ponte de aço', 'pontes de aço', 'estrutura de madeira', 'estruturas de madeira', 'sistema pré-moldado', 'sistemas pré-moldados', 'túnel submerso', 'túneis submersos',
    'engenharia costeira', 'proteção contra enchente', 'proteções contra enchentes', 'levantamento topográfico', 'análise sísmica', 'resposta estrutural', 'respostas estruturais', 'engenharia de fundações', 'estrutura hiperestática', 'estruturas hiperestáticas',
    'análise de estabilidade', 'carga de vento', 'cargas de vento', 'engenharia de minas', 'exploração de recurso natural', 'exploração de recursos naturais', 'equipamento de construção', 'equipamentos de construção', 'automação na construção',
    'planejamento de canteiro', 'planejamentos de canteiros', 'sistema hidráulico', 'sistemas hidráulicos', 'sistema elétrico predial', 'sistemas elétricos prediais', 'orçamento de obra', 'orçamentos de obras', 'logística de material', 'logísticas de materiais',
    'prevenção de desastres', 'infraestrutura crítica', 'infraestruturas críticas', 'ponte estaiada', 'pontes estaiadas', 'construção modular', 'construções modulares', 'pré-fabricação', 'isolamento acústico', 'isolamentos acústicos',
    'resíduo da construção', 'resíduos da construção', 'demolição', 'demolições', 'recuperação estrutural', 'recuperações estruturais', 'ensaio não destrutivo', 'ensaios não destrutivos', 'trinca', 'trincas', 'fissura', 'fissuras',
    'monitoramento estrutural', 'duto subterrâneo', 'dutos subterrâneos', 'bombeamento de concreto', 'concreto auto-adensável', 'concretos auto-adensáveis'
]


def mensagem_valida(mensagem):
    mensagem_normalizada = unidecode(mensagem).lower()
    for palavra in PALAVRAS_CHAVE_ENGENHARIA_MATEMATICA:
        if palavra in mensagem_normalizada:
            return True
    return False

def processar_mensagem(prompt, acao):
    mensagens = st.session_state['mensagens']
    
    if not mensagem_valida(prompt):
        resposta_nao_valida = "ERRO"
        mensagens.append({'role': 'assistant', 'type': 'text', 'content': resposta_nao_valida})
        st.session_state['prompt_input'] = ''
        st.session_state['mensagens'] = mensagens
        return

    nova_mensagem_usuario = {'role': 'user', 'type': 'text', 'content': prompt}
    mensagens.append(nova_mensagem_usuario)

    expressoes_criador = ["quem é seu criador", "quem te criou", "quem criou você", "quem é o seu criador"]

    if any(expressao in prompt.lower() for expressao in expressoes_criador):
        resposta_criador = "O meu criador foi o Davi Valerio."
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
    <h1 style='text-align: left; margin-bottom: 20px;'>IA <span style='font-size: 60px;'>TOP</span></h1>
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
