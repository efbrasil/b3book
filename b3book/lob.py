from enum import Enum
import numpy as np
import math
import os
import gzip
import csv
import pickle

from .single_lob import SingleLOB
from .functions import parse_csv_row

class LOB:
    def __init__(self, pinf = 0, psup = 100, ticksize = 1,
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

    def process_orders(self, limit):
        for order in self.orders:
            if order.prio_date > limit:
                break
            
            if self.last_mod and self.last_mod > order.prio_date:
                raise Exception('out of order order ({})'.format(order))
            
            self.last_mod = order.prio_date

            if self.status == 'closed' and order.event == 'trade':
                self.status = 'opening'

            if self.status == 'opening' and order.event != 'trade':
                # All pending trades should be completed before the market
                # opens
                self.check_trades()
                self.status = 'open'

            if order.event == 'trade' and self.status == 'opening':
                self.lob[order.side].process_pre_trade(order)

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
            best_buy_seq = self.lob['buy'].prio_queue[best_buy_pidx][0]
            best_buy_size = self.lob['buy'].db[best_buy_seq].size - self.lob['buy'].db[best_buy_seq].executed
    
            best_sell_seq = self.lob['sell'].prio_queue[best_sell_pidx][0]
            best_sell_size = self.lob['sell'].db[best_sell_seq].size - self.lob['sell'].db[best_sell_seq].executed
    
            last_mod = self.last_mod
            trade_size = min(best_buy_size, best_sell_size)
    
            self.lob['buy'].execute(best_buy_seq, trade_size, last_mod)
            self.lob['sell'].execute(best_sell_seq, trade_size, last_mod)

    def get_liquidity(self):
        liquidity = {'buy':  (np.array(self.lob['buy'].book)) * self.size_scale,
                     'sell': (np.array(self.lob['sell'].book)) * self.size_scale}
        
        idx = np.arange(self.booksize)
        prices = (self.pinf + idx * self.ticksize) * self.price_scale

        return prices, liquidity

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

