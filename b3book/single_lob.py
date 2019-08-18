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
        self.prio_queue = [deque() for x in range(self.booksize)]
        self.db = {}

        self.side = side

    def index(self, price):
        """Returns the index of a given price"""
        return(math.floor((price - self.pinf) / self.ticksize))

    def price(self, index):
        """Returns the lowest price of a given index"""
        return(self.pinf + index * self.ticksize)

    def add(self, order):
        """Add an order to the priority queue, to the database and to the book"""

        # Database
        dborder = DBOrder(size = order.size, executed = order.executed,
                          price = order.price, side = order.side)
        self.db[order.seq] = dborder
        
        # Priority Queue
        pidx = self.index(order.price)
        self.prio_queue[pidx].append(order.seq)

        # Book
        self.book[pidx] += (order.size - order.executed)

    def remove(self, seq):
        """Removes an order from the priority queue, database and from the book"""

        # Get current info about the order (from the DB)
        dborder = self.db[seq]
        dbprice = dborder.price
        dbremaining = dborder.size - dborder.executed
        pidx = self.index(dbprice)

        # Book
        if self.book[pidx] < dbremaining:
            raise Exception('negative order amount (seq = {})'.format(seq))

        self.book[pidx] -= dbremaining

        # Priority Queue
        self.prio_queue[pidx].remove(seq)

        # Database
        del self.db[seq]

    def update(self, order):
        """Updates an order in the database, the priority queue and the book"""

        # Removes the old order and adds the new one, keeping the executed amount
        if self.db[order.seq].size < order.executed:
            raise Exception('in update, executed > size')
        elif self.db[order.seq].size == order.executed:
            raise Exception('in update, executed == size')
        
        executed = self.db[order.seq].executed
        self.remove(order.seq)
        updated = copy(order)
        updated.executed = executed
        self.add(updated)
        # self.add(order)

    def execute(self, seq, executed, mod):
        """
        Executes part of an order, updating the database and the book.
        
        If the remaining is zero, remove from the database and from the priority queue
        """

        if executed <= 0:
            raise Exception('in execute(), executed <= 0')
        # Get current info about the order (from the DB)
        dborder = self.db[seq]
        dbprice = dborder.price
        dbremaining = dborder.size - dborder.executed
        pidx = self.index(dbprice)

        if executed > dbremaining:
            raise Exception('Executed amount > remaining ({})'.format(seq))

        elif executed == dbremaining:
            self.remove(seq)

        else:
            self.db[seq].executed += executed
            self.book[pidx] -= executed

    def process_new(self, order):

        if order.seq in self.db:
            raise Exception('new order already in db ({})'.format(order))

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
        
        # elif self.db[order.seq].executed != order.executed:
        #     raise Exception('executed amount changed in update ({})'.format(order))

        else:
            self.update(order)
        
    def process_pre_trade(self, order):

        if order.seq not in self.db:
            print('pre_open trade not in db ({})'.format(order))
            return
        
        elif self.db[order.seq].size != order.size:
            raise Exception('size changed in pre open trade ({})'.format(order))

        elif self.db[order.seq].price != order.price:
            # raise Exception('price changed in pre open trade ({})'.format(order))
            print('price changed in pre open trade ({})'.format(order))
            self.update(order)

        # Get current info about the order (from the DB)
        dborder = self.db[order.seq]
        dbprice = dborder.price
        dbremaining = dborder.size - dborder.executed
        pidx = self.index(dbprice)

        executed = order.executed - dborder.executed

        if executed > dbremaining:
            raise Exception('Pre trade executed amount > remaining ({})'.format(order))

        elif executed == dbremaining:
            self.remove(order.seq)

        else:
            self.db[order.seq].executed += executed
            self.book[pidx] -= executed
        
    def process_order(self, order):

        if order.executed > order.size:
            raise Exception('executed > size ({})'.format(order))

        if order.event == 'new':
            self.process_new(order)

        elif order.event == 'update':
            self.process_update(order)

        elif order.event == 'cancel':
            self.process_cancel(order)
            
        # elif order.event == 'trade':
        #     # self.process_pre_trade(order)
        #     if self.status == MarketStatus.opening:
        #         self.process_pre_trade(order)


        elif order.event == 'reentry':
            pass
            # self.process_update(order)


        else:
            print('unknown event ({})'.format(order))
            # raise Exception('unknown event ({})'.format(order))

    def snapshot(self):
        idx = np.where(self.book > 0)[0]
        prices = self.price(idx)
        sizes = self.book[idx]
        
        return sizes, prices

