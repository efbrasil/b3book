import b3book
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

import pdb
import importlib

lob = b3book.LOB()

# Opcao 1: Le os arquivos CSV (demora um pouco)
files = ['OFER_CPA_20190628.gz', 'OFER_VDA_20190628.gz']
lob.read_orders('BBDC4', files, 'data')
lob.save_orders('bbdc4_20190628.data')

# Opcao 2: Le um arquivo .data gerado anteriormente (mais rapido)
# lob.load_orders('bbdc4_20190628.data')

# Processa todas as ordens ate 16:45
lob.process_orders('16:54')

# Obtem as informacoes sobre o bid-ask spread entre 10:15 e 16:45
bas = lob.get_bas('10:15', '16:45')

