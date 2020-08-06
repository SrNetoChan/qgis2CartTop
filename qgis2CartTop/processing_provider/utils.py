from PyQt5.QtCore import QSettings

def get_postgres_connections():

    s = QSettings()
    s.beginGroup("PostgreSQL/connections")

    d = set([key.split('/')[0] for key in s.allKeys() if '/' in key])
    s.endGroup()

    return list(d)
