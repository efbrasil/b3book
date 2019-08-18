from datetime import datetime
import numpy as np

from .data_classes import B3Order
from .constants import events, sides, states

def parse_csv_row(row, price_scale, size_scale):
    ticker = row[1].strip()
    prio_date = datetime.strptime('{} {}'.format(row[11], row[6]),
                                  '%Y-%m-%d  %H:%M:%S.%f')
    seq = int(row[3])
    gen_id = int(row[4])
    side = sides[row[2]]
    event = events[int(row[5])]
    state = states[row[13]]
    condition = int(row[14])
    size = int(int(row[9]) / size_scale)
    executed = int(int(row[10]) / size_scale)

    price_str = row[8].strip()
    price = int(float(price_str) / price_scale)

    session_date = row[0]

    order = B3Order(prio_date, session_date, seq, side, event, state,
                    condition, price, size, executed, gen_id)

    return order, ticker

def plot_book(lob, plt, PLOT = True):
    buy = lob.lob['buy']
    i = np.arange(len(buy.book))
    prices = buy.price(i) * lob.price_scale
    total = sum(buy.book)
    plt.plot(prices, total - np.cumsum(buy.book))
    
    sell = lob.lob['sell']
    total = sum(sell.book)
    plt.plot(prices, np.cumsum(sell.book))

    best_buy_pidx  = np.where(lob.lob['buy'].book > 0)[0][-1]
    best_buy_price = prices[best_buy_pidx]

    best_sell_pidx = np.where(lob.lob['sell'].book > 0)[0][0]
    best_sell_price = prices[best_sell_pidx]

    mid = (best_buy_price + best_sell_price) / 2

    pmin = 0.98 * mid
    pmax = 1.02 * mid

    idx = np.where((prices >= pmin) & (prices <= pmax))
    smax = max(max(sum(buy.book) - np.cumsum(buy.book[idx])),
               max(np.cumsum(sell.book[idx])))
    
    plt.xlim((pmin, pmax))
    plt.ylim((0, smax))

    if PLOT:
        plt.show()
