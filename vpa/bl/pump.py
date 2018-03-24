from .base import BaseStrategy


class PumpBuyStrategy(BaseStrategy):
    """
    Watch for price rapidly increasing with volume supporting it.
    """
    NAME = 'pump'

    def decide(self, decision):
        decision.do = 1
        return decision
