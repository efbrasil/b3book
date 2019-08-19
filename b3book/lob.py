from enum import Enum
import numpy as np
import math
import os
import gzip
import csv
import pickle
from datetime import datetime, timedelta

from .single_lob import SingleLOB
from .functions import parse_csv_row

class LOB:
    def __init__(self, pinf = 0, psup = 100, ticksize = 1,
                 price_scale = 0.01, size_scale = 100,
                 initial_status = 'closed', use_b3_trades = 'preopen'):
        
        self.lob = {'buy' : SingleLOB(pinf, psup, ticksize, 'buy'),
                    'sell': SingleLOB(pinf, psup, ticksize, 'sell')}

        self.status = initial_status
        self.price_scale = price_scale
        self.size_scale = size_scale
        self.pinf = pinf
        self.psup = psup
        self.booksize = math.ceil((psup - pinf) / ticksize)
        self.ticksize = ticksize
        self.use_b3_trades = use_b3_trades

        self.last_mod = None
        self.session_date = None
        self.snapshot_times = []
        self.snapshots = []
        self.orders = []

    def read_orders(self, ticker, fnames,
                    data_dir = os.path.join(os.getcwd(), 'data')):
        for fname in fnames:
            full_fname = os.path.join(data_dir, fname)
            with gzip.open(full_fname, mode = 'rt') as csvfile:
                filtered = filter(lambda row: ticker in row, csvfile)
                csvreader = csv.reader(filtered, delimiter = ';')
                for row in csvreader:
                    if len(row) < 15:
                        continue
                    order, row_ticker = parse_csv_row(row, 
                                                      self.price_scale,
                                                      self.size_scale)
                    
                    if self.session_date == None:
                        self.session_date = order.session_date
                    elif self.session_date != order.session_date:
                        raise Exception(
                            'Orders from more than one sesssion ({})'.format(
                                order))
            
                    if row_ticker == ticker:
                        self.orders.append(order)
        
        self.orders.sort(key = lambda o: (o.prio_date, o.gen_id))

    def save_orders(self, fname,
                    data_dir = os.path.join(os.getcwd(), 'data')):

        with open(os.path.join(data_dir, fname), 'wb') as orders_file:
            pickle.dump(self.orders, orders_file)

    def load_orders(self, fname,
                    data_dir = os.path.join(os.getcwd(), 'data')):

        with open(os.path.join(data_dir, fname), 'rb') as orders_file:
            self.orders = pickle.load(orders_file)

        self.session_date = self.orders[0].session_date

    def process_orders(self, limit):
        if self.session_date == None:
            self.session_date = self.orders[0].session_date

        day_start = datetime.strptime('{} 00:00:01'.format(self.session_date),
                                      '%Y-%m-%d %H:%M:%S')
            
        for order in self.orders:
            if order.prio_date > limit:
                break

            if len(self.snapshot_times) > 0:
                if order.prio_date > self.snapshot_times[0]:
                    self.snapshots.append((self.snapshot_times[0],
                                           self.snapshot()))
                    self.snapshot_times = self.snapshot_times[1:]
            
            if self.last_mod and self.last_mod > order.prio_date:
                raise Exception('out of order order ({})'.format(order))
            
            self.last_mod = order.prio_date

            if (self.status == 'closed' and
                order.event == 'trade' and
                order.prio_date >= day_start and
                self.use_b3_trades != 'always'):
                self.status = 'opening'

            if self.status == 'opening' and order.event != 'trade':
                # All pending trades should be completed before the market
                # opens
                self.check_trades()
                self.status = 'open'

            if order.event == 'trade' and (self.status == 'opening' or self.use_b3_trades == 'always'):
                self.lob[order.side].process_trade(order)

            if order.event != 'trade':
                self.lob[order.side].process_order(order)

            if self.status == 'open':
                self.check_trades()

    def check_trades(self):
        while (len(self.lob['buy'].db) > 0) and (len(self.lob['sell'].db) > 0):
            best_buy_pidx  = np.where(self.lob['buy'].book > 0)[0][-1]
            best_buy_price = self.lob['buy'].price(best_buy_pidx)
    
            best_sell_pidx = np.where(self.lob['sell'].book > 0)[0][0]
            best_sell_price = self.lob['sell'].price(best_sell_pidx)
    
            if best_buy_price < best_sell_price:
                return best_buy_price, best_sell_price
            
            # If this is reached, than there is a trade pending
            best_buy_size = self.lob['buy'].book[best_buy_pidx]
            best_sell_size = self.lob['sell'].book[best_sell_pidx]
    
            last_mod = self.last_mod
            trade_size = min(best_buy_size, best_sell_size)

            self.lob['buy'].dec(best_buy_price, trade_size)
            self.lob['sell'].dec(best_sell_price, trade_size)
    
    def set_snapshot_times(self, snapshot_times):
        self.snapshot_times = []
        for s_time in snapshot_times:
            if isinstance(s_time, datetime):
                self.snapshot_times.append(s_time)
            elif isinstance(s_time, str):
                self.snapshot_times.append(datetime.strptime(
                    '{} {}'.format(self.session_date, s_time),
                    '%Y-%m-%d %H:%M:%S'))
        self.snapshot_times.sort()

    def set_snapshot_freq(self, interval,
                          first = '10:15:00', last = '16:45:00'):
        t0 = datetime.strptime('{} {}'.format(self.session_date, first),
                               '%Y-%m-%d %H:%M:%S')
        T  = datetime.strptime('{} {}'.format(self.session_date, last),
                               '%Y-%m-%d %H:%M:%S')

        s_times = []
        t = t0
        delta = timedelta(seconds = interval)
        
        while t <= T:
            s_times.append(t)
            t = t + delta

        self.set_snapshot_times(s_times)

    def snapshot(self):
        res = {}
        
        buy_sizes, buy_prices = self.lob['buy'].snapshot()
        buy_sizes = np.flip(buy_sizes) * self.size_scale
        buy_prices = np.flip(buy_prices) * self.price_scale
        
        sell_sizes, sell_prices = self.lob['sell'].snapshot()
        sell_sizes = sell_sizes * self.size_scale
        sell_prices = sell_prices * self.price_scale

        return {'buy_prices': buy_prices, 'buy_sizes' : buy_sizes,
                'sell_prices': sell_prices, 'sell_sizes' : sell_sizes,
                'best_buy' : buy_prices[0], 'best_sell' : sell_prices[0],
                'mid': (buy_prices[0] + sell_prices[0]) / 2,
                'last_order' : self.last_mod}

