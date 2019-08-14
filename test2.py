import b3book
import importlib
from datetime import datetime
import matplotlib.pyplot as plt
import pdb
import numpy as np

def plot_book (lob: b3book.LOB, PLOT = False):
    buy = lob.lob['buy']
    i = np.arange(len(buy.book))
    prices = buy.price(i) * lob.price_scale
    total = sum(buy.book)
    plt.plot(prices, total - np.cumsum(buy.book))
    
    sell = lob.lob['sell']
    total = sum(sell.book)
    plt.plot(prices, np.cumsum(sell.book))
    
    plt.xlim((36, 40))
    if PLOT:
        plt.show()

fnames = ['./MarketData/bbdc4_cpa', './MarketData/bbdc4_vda']
orders = b3book.read_orders_from_plain_files(fnames)

importlib.reload(b3book)
importlib.reload(b3book.functions)
importlib.reload(b3book.single_lob)
importlib.reload(b3book.lob)
importlib.reload(b3book)

limit = datetime.strptime('2019-06-26 10:30:00.000', '%Y-%m-%d  %H:%M:%S.%f')
pre = [o for o in orders if o.prio_date < limit]
lob = b3book.LOB(0, 7000, 1, 1 / 100, b3book.MarketStatus.opened)
lob.process_orders(pre)

plt.figure()
plot_book(lob, True)

