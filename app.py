#bibliotecas e funcoes
from flask import Flask, render_template
from CarregarDados import carregar_dados
import pickle

#inicializar o site(app)
app = Flask(__name__)

#endereço da homepage
@app.route('/')
def homepage():
    
    # Passa o retorno da funcao com os dados para o template html
    jogos = carregar_dados()
    
    return render_template('homepage.html', jogos=jogos)

#endereço dos detalhes do jogo escolhido ao clicar em homepage
@app.route('/jogo/<jogo_id>')
def estatisticas(jogo_id):
    
    # Passa o retorno da funcao com os dados para o template html
    jogos = carregar_dados()

    #carrega a ordem de colunas auto
    def carregar_colunas():
        
        with open('colunas_estatisticas.pkl', 'rb') as f:
            colunas = pickle.load(f)
        
        return colunas
    
    #carrega as colunas
    col_dados_ao_vivo = carregar_colunas()

    #especifica qual e o jogo_id
    if jogo_id in jogos:
        
        jogo_especifico = jogos[jogo_id]
    
        return render_template('estatisticas.html', jogo = jogo_especifico, col_dados_ao_vivo=col_dados_ao_vivo)
    
    else:
        return 'Não encontrado!' 

#pagina com as escalaçoes dos jogadores e os lesionados de cada time   
@app.route('/jogo/<jogo_id>/escalacao')
def escalacao(jogo_id):

    # Passa o retorno da funcao com os dados para o template html
    jogos = carregar_dados()
    
    #especifica qual e o jogo_id, e pega a escalaçao somente daquele jogo
    if jogo_id not in jogos:
        return "Jogo não encontrado", 404

    if jogo_id in jogos:

        escalacao = jogos[jogo_id]
    
    def obter_posicoes_por_linha(jogo, time='home'):
        
        posicoes = []
        
        for i in range(1, 6):
            
            chave = f"{time}_posição_{i}"
            
            if chave in jogo:
                jogadores = jogo[chave]
                
                #Garante que esteja como lista
                if isinstance(jogadores, str):
                    jogadores = [j.strip() for j in jogadores.split(',')]
                
                posicoes.append(jogadores)
        
        return posicoes
    
    posicoes_home = obter_posicoes_por_linha(escalacao, time='home')
    posicoes_away = obter_posicoes_por_linha(escalacao, time='away')

    return render_template('escalacao.html', jogo = escalacao, posicoes_home=posicoes_home, posicoes_away=posicoes_away, formacao_home=len(posicoes_home), formacao_away=len(posicoes_away), enumerate = enumerate)


#pagina com os confrontos historicos entre os dois times
@app.route('/jogo/<jogo_id>/confrontos')
def confrontos(jogo_id):
    
    #Passa o retorno da funcao com os dados para o template html
    jogos = carregar_dados()

    #especifica qual e o jogo_id, e pega os jogos historicos somente daqueles times
    if jogo_id in jogos:

        jogo = jogos[jogo_id]

    jogo_h2h = jogo['h2h']

    return render_template('confrontos.html', jogo = jogo, h2h = jogo_h2h)


# Rodar o site
if __name__ == '__main__':
    app.run(debug=True)  # Modo debug ativado
