import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import b3book

import importlib
importlib.reload(b3book)
importlib.reload(b3book.functions)
importlib.reload(b3book.lob)
importlib.reload(b3book)
importlib.reload(b3book.functions)
importlib.reload(b3book.lob)

# fnames = ['./MarketData/bbdc4_cpa', './MarketData/bbdc4_vda']
# orders = b3book.read_plain_orders(fnames)

# first_neg = pd.Timestamp('2019-06-26 10:03:00.002')
# buy_pre_neg = orders[(orders.side == 1) & (orders.prio_date < first_neg)]
# buy_pre_neg_s = buy_pre_neg[buy_pre_neg.preco > 37.74]

# bbook = b3book.LOB(0, 7000, 1, 1 / 100)
# bbook.process_orders(buy_pre_neg)
# bbook.plot()

limit = pd.Timestamp('2019-06-26 10:10:00')
o = orders[(orders.prio_date < limit)]
lob = b3book.LOB(0, 7000, 1, 1 / 100)
for _, order in o.iterrows():
    lob.process_order(order)

limit = pd.Timestamp('2019-06-26 15:00:00')
o = orders[(orders.prio_date < limit)]
lob = b3book.LOB(0, 7000, 1, 1 / 100)

count = 0
plt.figure()
plt.xlim((36, 40))
self = lob.lob['buy']
i = np.arange(len(self.book))
prices = self.price(i) * self.scale

for _, order in o.iterrows():
    lob.process_order(order)
    count = count + 1
    if ((count % 1000) == 0):
        import sys
        plt.clf()
        t = order['prio_date']
        print(t)
        sys.stdout.flush()
        
        self = lob.lob['buy']
        total = sum(self.book)
        plt.plot(prices, total - np.cumsum(self.book))

        self = lob.lob['sell']
        total = sum(self.book)
        plt.plot(prices, np.cumsum(self.book))

        plt.xlim((36, 40))
        plt.title(t)
        plt.draw()
        plt.show(block = False)
        plt.pause(0.001)

