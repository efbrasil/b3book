import pandas as pd
# from . import lob

from .constants import orders_names


def df_empty(columns, dtypes, index = None):
    assert len(columns) == len(dtypes)
    df = pd.DataFrame(index = index)
    for c, d in zip(columns, dtypes):
        df[c] = pd.Series(dtype = d)
    return df

def read_plain_orders(fnames, s = ';', cols = orders_names):
    orders = pd.DataFrame()
    for fname in fnames:
        new_df = pd.read_csv(fname, sep = s, names = cols)
        orders = orders.append(new_df, ignore_index = True)

    orders.ticker = orders.ticker.str.strip()
    orders.price = (orders.price * 100 + 0.0001).astype('int')

    orders = orders.assign(
        prio_date = pd.to_datetime(orders.order_date + ' ' + orders.prio_time),
        event = pd.Categorical(orders.ev_code),
        side = pd.Categorical(orders.cod_side))

    orders.event.cat.rename_categories({
        1 : 'new', 2 : 'update', 3 : 'cancel',
        4 : 'trade', 5 : 'reentry', 6 : 'newstop',
        7 : 'reject', 8 : 'removed', 9 : 'stopped',
        11 : 'expire'}, inplace = True)

    orders.side.cat.rename_categories({1: 'buy', 2: 'sell'}, inplace = True)

    orders = orders[['prio_date', 'seq', 'side', 'event', 'state',
                 'condition', 'price', 'size', 'executed', 'gen_id']]

    orders.sort_values(['prio_date', 'gen_id'], inplace = True)
    orders.reset_index(inplace = True)
    orders.drop(['index'], axis = 1, inplace = True)

    return orders
