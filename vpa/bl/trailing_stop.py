from .base import BaseStrategy


class TrailingStopSellStrategy(BaseStrategy):
    """
    Dynamic stop loss.
    """
    NAME = 'trailing_stop'
