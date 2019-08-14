from datetime import datetime
from dataclasses import dataclass

@dataclass
class B3Order:
    prio_date: datetime
    seq: int
    side: str
    event: str
    state: str
    condition: int
    price: int
    size: int
    executed: int
    gen_id: int

@dataclass
class DBOrder:
    """
    Single buy or sell order, potentially partially executed.
    
    Parameters
    ----------
    
    size : int
      current size of the order
    
    price : int
      current price of the orders (in cents)
    
    side : str
      order side ('buy' or 'sell')
    
    executed : int
      amount already executed
    """
    size: int
    executed: int
    price: int
    side: str

