import b3book
from datetime import datetime

import importlib
importlib.reload(b3book)
importlib.reload(b3book.functions)
importlib.reload(b3book.lob)
importlib.reload(b3book)
importlib.reload(b3book.functions)
importlib.reload(b3book.lob)

def run_book(lob : b3book.LOB, orders):
    count = 0
    for order in orders:
        lob.process_order(order)
        count = count + 1
        if ((count % 1000) == 0):
            print(order.prio_date)


fnames = ['./MarketData/bbdc4_cpa', './MarketData/bbdc4_vda']
orders = b3book.read_orders_from_plain_files(fnames)
limit = datetime.strptime('2019-06-26 10:30:00', '%Y-%m-%d %H:%M:%S')
pre = [o for o in orders if o.prio_date < limit]
lob = b3book.LOB(0, 7000, 1, 1 / 100)

run_book(lob, orders)

