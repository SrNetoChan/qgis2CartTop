from PyQt5.QtCore import QSettings
from json import load
import os

def get_postgres_connections():

    s = QSettings()
    s.beginGroup("PostgreSQL/connections")

    d = set([key.split('/')[0] for key in s.allKeys() if '/' in key])
    s.endGroup()

    return list(d)

def get_lista_codigos(nome_lista_codigos):
    listas_codigos_path = os.path.join(os.path.dirname( __file__ )
        , 'extras'
        , 'listas_codigos.json')
    with open(listas_codigos_path) as f:
            data = load(f)
    
    dict = data[nome_lista_codigos]
    
    return list(dict.keys()), list(dict.values()) 
