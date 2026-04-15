# src/quant_finance/instruments/equity/__init__.py
"""
Makes equity a proper subpackage and enables clean imports like:
    from quant_finance.instruments.equity import EuropeanCall, Equity
"""

from .equity import Equity
from .option import (
    EuropeanCall,
    EuropeanPut,
    AmericanCall,
    AmericanPut,
    DigitalCall,
    DigitalPut,
    BarrierCall,
    BarrierPut,
    LookbackCall,
    LookbackPut,
)
from .forward import Forward, ForwardSide

__all__ = [
    "Equity",
    "EuropeanCall",
    "EuropeanPut",
    "AmericanCall",
    "AmericanPut",
    "DigitalCall",
    "DigitalPut",
    "BarrierCall",
    "BarrierPut",
    "LookbackCall",
    "LookbackPut",
    "Forward",
    "ForwardSide",
]