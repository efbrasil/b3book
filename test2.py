import b3book
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

import pdb
import importlib

importlib.reload(b3book)
importlib.reload(b3book.functions)
importlib.reload(b3book.single_lob)
importlib.reload(b3book.lob)
importlib.reload(b3book)

nlob = b3book.LOB(pinf = 0, psup = 12000, ticksize = 1,
                 price_scale=0.01, size_scale=100,
                  initial_status='closed')
nlob.orders = myo
nlob.session_date = nlob.orders[0].session_date

files = ['OFER_CPA_20190628.gz', 'OFER_VDA_20190628.gz']
limit = datetime.strptime('2019-06-28 15:01:00.000', '%Y-%m-%d  %H:%M:%S.%f')
# lob.read_orders('BBDC4', files, 'data')
# lob.load_orders('bbdc4-20190228.data')
myo = nlob.orders
nlob.set_snapshot_freq(60*10)
nlob.process_orders(limit)
b3book.plot_book(lob, plt, True)

# Price impact
snap = lob.snapshot()
sizes = snap['buy_sizes']/100
prices = snap['buy_prices']
size = 17000

qts = np.array([], dtype = np.int64)
eps = np.array([])

qtds = np.linspace(1, 2500, 2500)
tpi = temp_impact(sizes, prices, qtds)
plt.plot(qtds, tpi)
plt.show()

# 0.00088

def temp_impact(sizes, prices, size):
    price = prices[0]
    eps = np.array([eff_price(sizes, prices, q) for q in qtds])
    return(np.abs(eps - price) / price)
    
def eff_price(sizes, prices, size):
    s = np.array(sizes)
    s[-1] = 0
    s = np.roll(s, 1)
    cs = np.cumsum(s)
    l1 = size - cs
    l2 = np.maximum(0, l1)
    l3 = np.minimum(l2, sizes)

    return(np.dot(l3, prices) / sum(l3))
    



# def accum(book, side):
#     if side == 'buy':
#         return (sum(book) - np.cumsum(book))
#     else:
#         return np.cumsum(book)
    
# def parse_book(slob):
#     side = 'buy'
#     slob = lob.lob[side]
#     idx = np.where(slob.book > 0)[0]
#     if side == 'buy':
#         idx = np.flip(idx)
#     price = slob.price(idx)
#     size = slob.book[idx]
#     plt.plot(price, np.cumsum(size))
#     plt.show()

