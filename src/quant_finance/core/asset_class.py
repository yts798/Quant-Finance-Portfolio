# core/asset_class.py
from enum import Enum, auto


class AssetClass(Enum):
    """Mutually exclusive top-level asset classes."""

    EQUITY      = auto()   # stocks, indices, single-name equity derivatives
    RATES       = auto()   # interest rates, bonds, swaps, swaptions, ...
    FX          = auto()   # foreign exchange spots, forwards, FX options
    CREDIT      = auto()   # CDS, defaultable bonds, credit indices
    COMMODITY   = auto()   # futures/options on oil, gold, ags, metals, ...
    INFLATION   = auto()   # inflation-linked bonds, YoY/II swaps
    HYBRID      = auto()   # convertibles, equity+rates hybrids, quantos, ...

    def __str__(self) -> str:
        return self.name.lower()