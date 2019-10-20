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
    def __init__(self, pinf = 0, psup = 12000, ticksize = 1,
                 price_scale = 0.01, size_scale = 100,
                 initial_status = 'closed'):
        
        self.lob = {'buy' : SingleLOB(pinf, psup, ticksize, 'buy'),
                    'sell': SingleLOB(pinf, psup, ticksize, 'sell')}

        self.status = initial_status
        self.price_scale = price_scale
        self.size_scale = size_scale
        self.pinf = pinf
        self.psup = psup
        self.booksize = math.ceil((psup - pinf) / ticksize)
        self.ticksize = ticksize

        self.last_mod = None
        self.session_date = None
        self.snapshot_times = []
        self.snapshots = []
        self.orders = []
        self.bas = []
        self.cur_bas = None

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

    def process_orders(self, tlimit = '16:45'):

        limit = datetime.strptime('{} {}'.format(self.session_date, tlimit),
                                  '%Y-%m-%d %H:%M')

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
            
            if self.status == 'closed' and order.event == 'trade':
                self.status = 'opening'

            if self.status == 'opening' and order.event != 'trade':
                self.status = 'open'

            self.lob[order.side].process_order(order)

            if (self.last_mod == None) or (order.prio_date > self.last_mod):
                self.last_mod = order.prio_date
                if (self.cur_bas != None):
                    self.bas.append(self.cur_bas)

            if self.status == 'open':
                best_bid_idx = np.where(self.lob['buy'].book > 0)[0][-1]
                best_ask_idx = np.where(self.lob['sell'].book > 0)[0][0]

                self.cur_bas = (order.prio_date,
                                self.lob['buy'].price(best_bid_idx),
                                self.lob['buy'].book[best_bid_idx],
                                self.lob['sell'].price(best_ask_idx),
                                self.lob['sell'].book[best_ask_idx])

    def get_bas(self, tlinf = '10:15', tlsup = '16:54'):
        linf = datetime.strptime('{} {}'.format(self.session_date, tlinf), '%Y-%m-%d %H:%M')
        lsup = datetime.strptime('{} {}'.format(self.session_date, tlsup), '%Y-%m-%d %H:%M')

        tmp = {'time' : np.array([e[0] for e in self.bas]),
               'bid_price' : np.array([e[1] for e in self.bas]),
               'bid_size' : np.array([e[2] for e in self.bas]),
               'ask_price' : np.array([e[3] for e in self.bas]),
               'ask_size' : np.array([e[4] for e in self.bas])}
        
        idx = (tmp['time'] >= linf) & (tmp['time'] <= lsup)

        return {'time' : tmp['time'][idx],
                'bid_price' : tmp['bid_price'][idx],
                'bid_size' : tmp['bid_size'][idx],
                'ask_price' : tmp['ask_price'][idx],
                'ask_size' : tmp['ask_size'][idx]}
        
    def get_liquidity(self):
        liquidity = {'buy':  (np.array(self.lob['buy'].book)) * self.size_scale,
                     'sell': (np.array(self.lob['sell'].book)) * self.size_scale}
        
        idx = np.arange(self.booksize)
        prices = (self.pinf + idx * self.ticksize) * self.price_scale

        return prices, liquidity

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

