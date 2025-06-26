#bibliotecas
import pandas as pd
import pickle
import sqlite3
import json

#importando funçoes que raspam os dados
from PegarIDs_ao_vivo import pegar_ID_ao_vivo
from Raspar_ao_vivo import Raspar_dados_paralelos
from Raspar_squad import Raspar_squads_paralelos
from Raspar_lesao import processar_lesioandos_paralelo
from Raspar_H2H import Raspar_h2h_paralelo

#create table dinamico
#funcao que cria uma tabela no banco com base nas colunas do DataFrame e exclui existentes
def criar_tabela_dinamica(df, conn, nome_tabela='estatisticas_jogos'):

    #conecta com o banco
    cursor = conn.cursor()
    
    #remove tabela se existir
    print(f"Removendo tabela existente: {nome_tabela}")
    cursor.execute(f"DROP TABLE IF EXISTS {nome_tabela}")
    
    colunas_sql = []
    
    #trata as colunas
    for col in df.columns:
        col_sanitizado = col.replace('"', '')
        colunas_sql.append(f'"{col_sanitizado}" TEXT')

    #cria a tabela com as colunas na ordem do DF
    comando_sql = f"CREATE TABLE {nome_tabela} ({', '.join(colunas_sql)})"
    print(f"Criando nova tabela com {len(colunas_sql)} colunas.")
    cursor.execute(comando_sql)
    
    #salva no banco
    conn.commit()
    print(f"Tabela '{nome_tabela}' criada com sucesso.")

#funcao principal que roda em loop pegando os jogos ao vivo
def main():

    try:
            
        #pegar_id_ao_vivo
        dic_ID = pegar_ID_ao_vivo()

        #se nao achar retorna vazio e com msg de erro
        if not dic_ID:
            print("Nenhum ID de jogo encontrado.")
            return
        
        print(f"Total de jogos ao vivo encontrados: {len(dic_ID)}")

        #raspar ao vivo / chama a funcao que raspas as estatisticas
        dic_dados = Raspar_dados_paralelos(dic_ID)
        print("Estatísticas ao vivo raspadas.")

        #squad / chama a funcao que raspa as escalaçoes
        dic_squad_home, dic_squad_away = Raspar_squads_paralelos(dic_ID)
        print("Escalações raspadas.")

        #lesao / chama a funcao que raspa os lesionados
        dic_home, dic_away = processar_lesioandos_paralelo(dic_ID)
        print("Dados de jogadores lesionados raspados.")

        #h2h / chama a funcao que raspa os confrontos diretos historicos
        dic_res = Raspar_h2h_paralelo(dic_ID)
        print("Confrontos diretos (H2H) raspados.")
        
        #passando value do dic(que contem od IDs) para um lista
        lista_ID = list(dic_ID.values())

        #Lista para armazenar todos os dados
        lista_completa = []

        #Monta a linha completa por jogo
        for match_id in lista_ID:
            
            jogo = {}
            
            jogo['Match ID'] = match_id

            dados = dic_dados.get(match_id, {})
            
            jogo.update(dados)
            
            #adiciona a escalaçao home
            for key, jogadores in dic_squad_home.get(match_id, {}).items():
                jogo[f"home_{key}"] = jogadores

            #adiciona a escalaçao away    
            for key, jogadores in dic_squad_away.get(match_id, {}).items():
                jogo[f"away_{key}"] = jogadores

            #adicina os lesionados home e away
            jogo['Lesionados Casa'] = dic_home.get(match_id, 'Nenhum')
            jogo['Lesionados Visitante'] = dic_away.get(match_id, 'Nenhum')

            #adiciona por ultimo o h2h
            jogo['h2h'] = dic_res.get(match_id, {})

            lista_completa.append(jogo)
            
            print(f"Total de jogos processados: {len(lista_completa)}")

        #listas de colunas na ordem da raspagem:
        col_dados_ao_vivo = []
        col_escala = []

        #classifica as colunas dos jogos para organizar dps
        for jogo in lista_completa:
            
            for k in jogo.keys():
                
                if k == 'Match ID' or k in ['Lesionados Casa', 'Lesionados Visitante', 'h2h']:
                    continue
                
                elif k.startswith('home_posição_') or k.startswith('away_posição_'):
                    
                    if k not in col_escala:
                        col_escala.append(k)
                
                else:
                    if k not in col_dados_ao_vivo:
                        col_dados_ao_vivo.append(k)
        
        #colunas na ordem, match_id fixo no inicio, dps as outras na ordem
        colunas_ordenadas = (
            ['Match ID'] +
            col_dados_ao_vivo +
            col_escala +
            ['Lesionados Casa', 'Lesionados Visitante', 'h2h']
        )

        print(f"Total de colunas na tabela: {len(colunas_ordenadas)}")
        
        #serializa os dic e listas...
        for jogo in lista_completa:
            
            for k, v in jogo.items():
                
                if isinstance(v, list):
                    jogo[k] = ', '.join(map(str, v))
                
                elif isinstance(v, dict):
                    jogo[k] = json.dumps(v, ensure_ascii=False)

        #cria o DF
        df = pd.DataFrame(lista_completa)

        #organiza as colunas exixtentes
        colunas_existentes = [col for col in colunas_ordenadas if col in df.columns]
        df = df[colunas_existentes]

        #salva o conteudo do DF no banco sqlite
        try:

            #conecta com o banco
            conn = sqlite3.connect('estatisticas.db')

            #Cria a tabela dinamicamente com as colunas atuais e ordenadas do dataframe
            criar_tabela_dinamica(df, conn)

            #salva
            df.to_sql('estatisticas_jogos', conn, if_exists='append', index=False)

            #salva a ordem de colunas para usar depois
            with open('colunas_estatisticas.pkl', 'wb') as f:
                pickle.dump(col_dados_ao_vivo, f)
        
        #msg caso tenha erro
        except Exception as e:
            print(f"Falha ao salvar no banco: {e}")
        
        finally:
            #fecha a conexao
            conn.close()

    except KeyboardInterrupt:
        print("Extração interrompida manualmente.")

if __name__ == "__main__":
    main()