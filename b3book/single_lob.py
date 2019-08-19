import numpy as np
import math
from collections import deque
from copy import copy

from .data_classes import B3Order, DBOrder

class SingleLOB:
    def __init__(self, pinf, psup, ticksize, side):
        self.pinf = pinf
        self.psup = psup
        self.ticksize = ticksize

        self.booksize = math.ceil((psup - pinf) / ticksize)
        self.book = np.zeros(self.booksize, dtype = 'int')
        # self.prio_queue = [deque() for x in range(self.booksize)]
        self.db = {}

        self.side = side

    def index(self, price):
        """Returns the index of a given price"""
        return(math.floor((price - self.pinf) / self.ticksize))

    def price(self, index):
        """Returns the lowest price of a given index"""
        return(self.pinf + index * self.ticksize)

    def inc(self, price, amount):
        pidx = self.index(price)
        self.book[pidx] += amount

    def dec(self, price, amount):
        pidx = self.index(price)
        if self.book[pidx] < amount:
            # print('book with negative size (price = {})'.format(price))
            # raise Exception('book with negative size (price = {})'.format(price))
            self.book[pidx] = 0
        else:
            self.book[pidx] -= amount

    def process_new(self, order):
        if order.seq in self.db:
            raise Exception('new order already in db ({})'.format(order))

        self.db[order.seq] = DBOrder(size = order.size,
                                     executed = order.executed,
                                     price = order.price,
                                     side = order.side)
        self.inc(order.price, order.size - order.executed)

    def process_cancel(self, order):
        if order.seq not in self.db:
            # print('cancelled order not in db ({})'.format(order))
            return
        
        del self.db[order.seq]
        self.dec(order.price, order.size - order.executed)

    def process_update(self, order):
        if order.seq not in self.db:
            self.process_new(order)
            return

        old_price = self.db[order.seq].price
        old_size = self.db[order.seq].size
        self.db[order.seq] = DBOrder(size = order.size,
                                     executed = order.executed,
                                     price = order.price,
                                     side = order.side)
        amount = old_size - order.executed
        self.dec(old_price, amount)
        self.inc(order.price, amount)
        
    def process_trade(self, order):
        if order.seq not in self.db:
            self.process_new(order)
            return
        
        elif self.db[order.seq].size != order.size:
            raise Exception('size changed in pre open trade ({})'.format(order))

        elif self.db[order.seq].price != order.price:
            print('price changed in pre open trade ({})'.format(order))
            self.db[order.seq] = DBOrder(size = order.size,
                                         executed = order.executed,
                                         price = order.price,
                                         side = order.side)

        amount = order.executed - self.db[order.seq].executed
        self.dec(order.price, amount)

        if order.size == order.executed:
            del self.db[order.seq]
        else:
            self.db[order.seq] = DBOrder(size = order.size,
                                         executed = order.executed,
                                         price = order.price,
                                         side = order.side)
        
    def process_order(self, order):
        if order.executed > order.size:
            raise Exception('executed > size ({})'.format(order))

        self.cur_order = order
        if order.event == 'new':
            self.process_new(order)

        elif order.event == 'update':
            self.process_update(order)

        elif order.event == 'cancel':
            self.process_cancel(order)

        elif order.event == 'trade':
            self.process_trade(order)
            
        elif order.event == 'reentry':
            self.process_update(order)

        else:
            # print('unknown event ({})'.format(order))
            raise Exception('unknown event ({})'.format(order))

    def snapshot(self):
        idx = np.where(self.book > 0)[0]
        prices = self.price(idx)
        sizes = self.book[idx]
        
        return sizes, prices

