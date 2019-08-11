import math
import numpy as np
import matplotlib.pyplot as plt
import pdb

class Order:
    def __init__(self, size, price, side, mod, executed = 0):
        self.size = size
        self.executed = executed
        self.price = price
        self.side = side
        self.mod = mod
    
    def execute(self, size, mod):
        self.executed += size
        self.mod = mod

    def update(self, size, price, mod):
        self.size = size
        self.price = price
        self.mod = mod

    def remaining(self):
        return (self.size - self.executed)

    def __repr__(self):
        return('<Order (side = {}, size = {}, executed = {}, price = {})'.format(
            self.side, self.size, self.executed, self.price))

class SingleLOB:
    def __init__(self, pinf, psup, ticksize, scale, side):
        self.pinf = pinf
        self.psup = psup
        self.ticksize = ticksize
        self.scale = scale

        self.booksize = math.ceil((psup - pinf) / ticksize)
        self.book = np.zeros(self.booksize, dtype = 'int')
        self.db = {}

        self.side = side

    def plot(self):
        plt.figure()
        i = np.arange(len(self.book))
        prices = self.price(i) * self.scale
        plt.bar(prices, self.book)
        plt.show()

        plt.figure()
        total = sum(self.book)
        plt.plot(prices, total - np.cumsum(self.book))
        plt.show()


    def index(self, price):
        return(math.floor((price - self.pinf) / self.ticksize))

    def price(self, index):
        return(self.pinf + index * self.ticksize)

    def add(self, price, size):
        idx = self.index(price)
        self.book[idx] += size

    def remove(self, price, size):
        idx = self.index(price)
        self.book[idx] -= size

    def process_check(self, order):
        seq, mod, side, event = order[['seq', 'prio_date', 'side', 'event']]
        size, executed, price = order[['size', 'executed', 'price']]
        if seq in self.db:
            cur_price = self.db[seq].price
            cur_size = self.db[seq].size
            cur_executed = self.db[seq].executed

        if executed > size:
            raise Exception('executed > size')

        if event == 'new':
            if seq in self.db:
                raise Exception('new order already in db')
            if executed != 0:
                raise Exception('new order with >0 executed')
        elif event == 'update':
            if seq in self.db:
                cur_executed = self.db[seq].executed
                if cur_executed != executed:
                    raise Exception('executed amount changed in update')
        elif event == 'cancel':
            # if seq not in self.db:
            #     # raise Exception('canceled order not in db({}/{})'.format(
            #     #     order['side'], order['seq']))
            #     pass
            # else:
            if seq in self.db:
                if ((cur_price != price) or(cur_size != size) or (cur_executed != executed)):
                    raise Exception('changes in cancelation')
        elif event == 'trade':
            if seq not in self.db:
                raise Exception('trade of order not in db')
            if cur_executed >= executed:
                raise Exception('negative (or zero) trade')
            if ((cur_price != price) or(cur_size != size)):
                raise Exception('changes in trade')
            if executed > size:
                raise Exception('trade with executed > size')

    def process_new(self, order):
        seq, mod, side = order[['seq', 'prio_date', 'side']]
        size, executed, price = order[['size', 'executed', 'price']]
        remaining = size - executed

        self.db[seq] = Order(size, price, side, mod)
        self.add(price, remaining)

    def process_update(self, order):
        seq, mod, side = order[['seq', 'prio_date', 'side']]
        size, executed, price = order[['size', 'executed', 'price']]
        remaining = size - executed

        if seq in self.db:
            cur_price = self.db[seq].price
            cur_remaining = self.db[seq].remaining()
            self.remove(cur_price, cur_remaining)
            self.db[seq].update(size, price, mod)
        else:
            self.db[seq] = Order(size, price, side, mod, executed)

        self.add(price, remaining)

    def process_cancel(self, order):
        seq, mod, side = order[['seq', 'prio_date', 'side']]
        size, executed, price = order[['size', 'executed', 'price']]
        remaining = size - executed

        if seq in self.db:
            self.remove(price, remaining)
            del self.db[seq]

    def process_trade(self, order):
        seq, mod, side = order[['seq', 'prio_date', 'side']]
        size, executed, price = order[['size', 'executed', 'price']]
        remaining = size - executed

        amount = executed - self.db[seq].executed

        self.db[seq].execute(amount, mod)
        self.remove(price, amount)

        return amount

#     def process_orders(self, orders):
#         amount = 0
#         trades = 0
#         for i, order in orders.iterrows():
#             self.process_check(order)

#             if order['event'] == 'new':
#                 self.process_new(order)
#             elif order['event'] == 'update':
#                 self.process_update(order)
#             elif order['event'] == 'cancel':
#                 self.process_cancel(order)
#             elif order['event'] == 'trade':
#                 trades += 1
#                 amount += self.process_trade(order)
# #            elif:
# #                raise Exception('Evento nao tratado')
#         print('trades = {}\namount = {}'.format(trades, amount))

    def process_order(self, order):
        self.process_check(order)
        if order['event'] == 'new':
            self.process_new(order)
        elif order['event'] == 'update':
            self.process_update(order)
        elif order['event'] == 'cancel':
            self.process_cancel(order)
        elif order['event'] == 'trade':
            self.process_trade(order)
        # elif:
        #     raise Exception('Evento nao tratado')

class LOB:
    def __init__(self, pinf, psup, ticksize, scale):
        self.lob = {'buy' : SingleLOB(pinf, psup,
                                      ticksize, scale, 'buy'),
                    'sell': SingleLOB(pinf, psup,
                                      ticksize, scale, 'buy')}

    def process_order(self, order):
        seq, mod, side = order[['seq', 'prio_date', 'side']]
        self.lob[side].process_order(order)
