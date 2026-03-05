# src/quant_finance/instruments/equity/__init__.py
"""
Makes equity a proper subpackage and enables clean imports like:
    from quant_finance.instruments.equity import EuropeanCall
"""

from .european_call import EuropeanCall
from .european_put import EuropeanPut
from .american_call import AmericanCall
from .american_put import AmericanPut

__all__ = [
    "EuropeanCall",
    "EuropeanPut",
    "AmericanCall",
    "AmericanPut",
]