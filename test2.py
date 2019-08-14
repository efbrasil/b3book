import b3book
import importlib
from datetime import datetime
import matplotlib.pyplot as plt
import pdb
import numpy as np

def run_book(lob: b3book.LOB, orders):
    count = 0
    for order in orders:
        # if (order.seq == 90685242918) and (order.gen_id == 17303381):
        #     pdb.set_trace()
        lob.process_order(order)
        # count = count + 1
        # if ((count % 1000) == 0):
        #     print(order.prio_date)

def plot_book (lob: b3book.LOB, PLOT = False):
    buy = lob.lob['buy']
    i = np.arange(len(buy.book))
    prices = buy.price(i) * buy.scale
    total = sum(buy.book)
    plt.plot(prices, total - np.cumsum(buy.book))
    
    sell = lob.lob['sell']
    total = sum(sell.book)
    plt.plot(prices, np.cumsum(sell.book))
    
    plt.xlim((36, 40))
    if PLOT:
        plt.show()

importlib.reload(b3book)
importlib.reload(b3book.functions)
importlib.reload(b3book.lob)
importlib.reload(b3book)
importlib.reload(b3book.functions)
importlib.reload(b3book.lob)

fnames = ['./MarketData/bbdc4_cpa', './MarketData/bbdc4_vda']
orders = b3book.read_orders_from_plain_files(fnames)
limit = datetime.strptime('2019-06-26 10:30:00.000', '%Y-%m-%d  %H:%M:%S.%f')
pre = [o for o in orders if o.prio_date < limit]

lob = b3book.LOB(0, 7000, 1, 1 / 100, b3book.MarketStatus.opened)

run_book(lob, pre)

plt.figure()
plot_book(lob, True)

