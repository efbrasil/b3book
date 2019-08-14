from enum import Enum
import numpy as np

from .single_lob import SingleLOB

class MarketStatus(Enum):
    closed = 0
    opening = 1
    opened = 2

class LOB:
    def __init__(self, pinf, psup, ticksize, scale, status = MarketStatus.closed):
        self.lob = {'buy' : SingleLOB(pinf, psup,
                                      ticksize, scale, 'buy'),
                    'sell': SingleLOB(pinf, psup,
                                      ticksize, scale, 'buy')}

        self.last_mod = None
        self.status = MarketStatus.closed

    def process_order(self, order):
        self.last_mod = order.prio_date

        if self.status == MarketStatus.closed and order.event == 'trade':
            self.status = MarketStatus.opening

        if self.status == MarketStatus.opening and order.event != 'trade':
            self.status = MarketStatus.opened

        if order.event == 'trade' and self.status == MarketStatus.opening:
            self.lob[order.side].process_pre_trade(order)
        
        if order.event != 'trade':
            self.lob[order.side].process_order(order)

        if self.status == MarketStatus.opened:
            self.check_trades()

    def check_trades(self):
        while (len(self.lob['buy'].db) > 0) and (len(self.lob['sell'].db) > 0):
            # pdb.set_trace()
            best_buy_pidx  = np.where(self.lob['buy'].book > 0)[0][-1]
            best_buy_price = self.lob['buy'].price(best_buy_pidx)
    
            best_sell_pidx = np.where(self.lob['sell'].book > 0)[0][0]
            best_sell_price = self.lob['sell'].price(best_sell_pidx)
    
            if best_buy_price < best_sell_price:
                break
            
            # If this is reached, than there is a trade pending
            best_buy_seq = self.lob['buy'].prio_queue[best_buy_pidx][0]
            best_buy_size = self.lob['buy'].db[best_buy_seq].size - self.lob['buy'].db[best_buy_seq].executed
    
            best_sell_seq = self.lob['sell'].prio_queue[best_sell_pidx][0]
            best_sell_size = self.lob['sell'].db[best_sell_seq].size - self.lob['sell'].db[best_sell_seq].executed
    
            last_mod = self.last_mod
            trade_size = min(best_buy_size, best_sell_size)
    
            self.lob['buy'].execute(best_buy_seq, trade_size, last_mod)
            self.lob['sell'].execute(best_sell_seq, trade_size, last_mod)
            # print('trade: {}'.format(trade_size))
    
