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
        self.db = {}

        self.side = side

    def index(self, price):
        """Returns the index of a given price"""
        return(math.floor((price - self.pinf) / self.ticksize))

    def price(self, index):
        """Returns the lowest price of a given index"""
        return(self.pinf + index * self.ticksize)

    def add(self, order):
        """Add an order to the database and to the book"""

        if (self.side == 'sell') and (order.price == 0):
            # print('sell order with price = 0 ({})'.format(order))
            return

        # Database
        dborder = DBOrder(size = order.size, executed = order.executed,
                          price = order.price, side = order.side)
        self.db[order.seq] = dborder
        
        # Book
        pidx = self.index(dborder.price)
        self.book[pidx] += (order.size - order.executed)

    def remove(self, seq):
        """Removes an order from the database and from the book"""

        # Get current info about the order (from the DB)
        dborder = self.db[seq]
        dbprice = dborder.price
        dbremaining = dborder.size - dborder.executed
        pidx = self.index(dbprice)

        # Book
        if self.book[pidx] < dbremaining:
            raise Exception('negative order amount (seq = {})'.format(seq))

        self.book[pidx] -= dbremaining

        # Database
        del self.db[seq]

    def process_new(self, order):

        if order.seq in self.db:
            # print('new order already in db ({})'.format(order))
            self.remove(order.seq)

        if order.executed != 0:
            raise Exception('new order with >0 executed({})'.format(order))

        self.add(order)

    def process_cancel(self, order):

        if order.seq not in self.db:
            # print('cancel not in db ({})'.format(order))
            pass

        else:
            self.remove(order.seq)

    def process_update(self, order):

        if order.seq not in self.db:
            # print('update not in db ({})'.format(order))
            self.add(order)
            return
        
        # elif self.db[order.seq].executed != order.executed:
        #     raise Exception('executed amount changed in update ({})'.format(order))

        self.remove(order.seq)
        self.add(order)
        
    def process_trade(self, order):

        if order.seq not in self.db:
            # print('trade not in db ({})'.format(order))
            self.add(order)
            return
        
        elif self.db[order.seq].size != order.size:
            raise Exception('size changed in trade ({})'.format(order))

        elif self.db[order.seq].price != order.price:
            # print('price changed in trade ({})'.format(order))
            pass

        self.remove(order.seq)
        self.add(order)
        
    def process_order(self, order):

        if order.executed > order.size:
            raise Exception('executed > size ({})'.format(order))

        if order.event == 'new':
            self.process_new(order)

        elif order.event == 'update':
            self.process_update(order)

        elif order.event == 'cancel':
            self.process_cancel(order)

        elif order.event == 'trade':
            self.process_trade(order)
            
        elif order.event == 'reentry':
            pass

        elif order.event == 'expire':
            self.process_cancel(order)

        else:
            print('unknown event ({})'.format(order))

    def snapshot(self):
        idx = np.where(self.book > 0)[0]
        prices = self.price(idx)
        sizes = self.book[idx]
        
        return sizes, prices

