import math
import numpy as np
import matplotlib.pyplot as plt
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
# import pdb

@dataclass
class B3Order:
    prio_date: datetime
    seq: int
    side: str
    event: str
    state: str
    condition: int
    price: int
    size: int
    executed: int
    gen_id: int

class Order:
    """
    Single buy or sell order, potentially partially executed.
    
    Parameters
    ----------
    
    size : int
      current size of the order
    
    price : int
      current price of the orders (in cents)
    
    side : str
      order side ('buy' or 'sell')
    
    mod : datetime.datetime
      timestamp of last modification
    
    executed : int
      amount already executed
    """
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
        if self.book[idx] < size:
            print('negative order amount (price = {})'.format(price))
        self.book[idx] -= size

    def process_check(self, order):
        if order.seq in self.db:
            cur_price = self.db[order.seq].price
            cur_size = self.db[order.seq].size
            cur_executed = self.db[order.seq].executed

        if order.executed > order.size:
            raise Exception('executed > size')

        if order.event == 'new':
            if order.seq in self.db:
                raise Exception('new order already in db')
            if order.executed != 0:
                raise Exception('new order with >0 executed')
        elif order.event == 'update':
            if order.seq in self.db:
                cur_executed = self.db[order.seq].executed
                if cur_executed != order.executed:
                    raise Exception('executed amount changed in update')
        elif order.event == 'trade':
            if order.seq not in self.db:
                raise Exception('trade of order not in db {} {}'.format(order.side, order.seq))
            if cur_executed >= order.executed:
                raise Exception('negative (or zero) trade')
            # if ((cur_price != price) or(cur_size != size)):
            #     raise Exception('changes in trade {}/{}'.format(side, seq))
            if order.executed > order.size:
                raise Exception('trade with executed > size')

    def process_new(self, order):
        remaining = order.size - order.executed

        self.db[order.seq] = Order(order.size, order.price, order.side, order.prio_date)
        self.add(order.price, remaining)

    def process_update(self, order):
        remaining = order.size - order.executed

        if order.seq in self.db:
            cur_price = self.db[order.seq].price
            cur_remaining = self.db[order.seq].remaining()
            self.remove(cur_price, cur_remaining)
            self.db[order.seq].update(order.size, order.price, order.prio_date)
        else:
            self.db[order.seq] = Order(order.size, order.price, order.side, order.prio_date, order.executed)

        self.add(order.price, remaining)

    def process_cancel(self, order):
        if order.seq in self.db:
            remaining = self.db[order.seq].remaining()
            price = self.db[order.seq].price
            self.remove(price, remaining)
            del self.db[order.seq]

    def process_trade(self, order):
        # TODO: remove order from db if completely executed
        amount = order.executed - self.db[order.seq].executed

        self.db[order.seq].execute(amount, order.prio_date)
        self.remove(order.price, amount)

        return amount

    def process_order(self, order):
        self.process_check(order)
        if order.event == 'new':
            self.process_new(order)
        elif order.event == 'update':
            self.process_update(order)
        elif order.event == 'cancel':
            self.process_cancel(order)
        elif order.event == 'trade':
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
        self.lob[order.side].process_order(order)
