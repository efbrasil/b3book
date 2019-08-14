import csv
from datetime import datetime

from .data_classes import B3Order
from .constants import events, sides, states

def read_orders_from_plain_files(fnames):
    orders = []

    for fname in fnames:
        with open(fname, 'r') as csvfile:
            csvreader = csv.reader(csvfile, delimiter = ';')
            for row in csvreader:
                ticker = row[1].strip()

                prio_date = datetime.strptime('{} {}'.format(row[11], row[6]),
                                              '%Y-%m-%d  %H:%M:%S.%f')
                seq = int(row[3])
                gen_id = int(row[4])
                side = sides[row[2]]
                event = events[int(row[5])]
                state = states[row[13]]
                condition = int(row[14])
                size = int(row[9])
                executed = int(row[10])

                price_str = row[8].strip()
                price_dec = price_str.index('.')
                price = 100 * int(price_str[:price_dec]) + int(price_str[price_dec+1:price_dec+3])

                order = B3Order(prio_date, seq, side, event, state,
                                condition, price, size, executed, gen_id)
                orders.append(order)

    orders.sort(key = lambda o: (o.prio_date, o.gen_id))
    return orders
