import csv
from datetime import datetime
from .lob import B3Order

def read_orders_from_plain_files(fnames):
    orders = []
    events = {1 : 'new', 2 : 'update', 3 : 'cancel', 4 : 'trade', 5 : 'reentry', 6 : 'newstop', 7 : 'reject', 8 : 'removed', 9 : 'stopped', 11 : 'expire'}
    sides = {'1' : 'buy', '2' : 'sell'}
    states = {'0' : 'new', '1' : 'partial', '2' : 'executed', '4' : 'cancelled', '5' : 'modified', '8' : 'rejected', 'C' : 'expired'}

    for fname in fnames:
        with open(fname, 'r') as csvfile:
            csvreader = csv.reader(csvfile, delimiter = ';')
            for row in csvreader:
                ticker = row[1].strip()

                prio_date = datetime.strptime('{} {}'.format(row[11], row[6]), '%Y-%m-%d  %H:%M:%S.%f')
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

                order = B3Order(prio_date, seq, side, event, state, condition, price, size, executed, gen_id)
                orders.append(order)

    orders.sort(key = lambda o: (o.prio_date, o.gen_id))
    return orders