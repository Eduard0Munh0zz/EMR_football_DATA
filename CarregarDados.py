#bibliotecas
import pandas as pd
import sqlite3
import json

#funcao que pega os dados
def carregar_dados():

    dados = {}
    
    #conecta no banco
    conn = sqlite3.connect('estatisticas.db')

    #pega toda a tabela do banco como DataFrame
    df = pd.read_sql_query("SELECT * FROM estatisticas_jogos", conn)

    #fecha
    conn.close()

    #trata a coluna tempo para exibir se esta ao vivo ou ja foi encerrado o jogo!
    if 'tempo' in df.columns:
        
        df['tempo'] = df['tempo'].astype(str)
        df['tempo_modificado'] = df['tempo'].apply(lambda x: f"{x} (Finalizado)" if x == '90:00' else f"{x} (Ao vivo)")
    
    else:
        
        df['tempo_modificado'] = None

    #organiza dinamicamente as colunas do DF, para evitar quebras no futuro
    for _, row in df.iterrows():
        
        jogo_info = {}

        for col in df.columns:
           
            valor = row[col]

            #Se for coluna com JSON serializado, desserializa
            if col in ['Lesionados Casa', 'Lesionados Visitante', 'h2h']:
                
                try:
                    valor = json.loads(valor) if valor else []
               
                except Exception:
                    pass

            #Para cada coluna tempo, use a versão modificada
            if col == 'tempo':
                valor = row.get('tempo_modificado', valor)
            
            jogo_info[col] = valor

        #Usa 'Match ID' como chave no dict principal
        chave = jogo_info.get('Match ID')
        
        if chave:
            dados[chave] = jogo_info

    return dados