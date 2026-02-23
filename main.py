# main.py
from datetime import date, timedelta
import argparse
import yaml
from dataclasses import dataclass
from typing import List, Dict, Any

from src.quant_finance.core.base_instrument import MarketDataSnapshot
from src.quant_finance.core.base_pricer import BasePricer
from src.quant_finance.instruments.equity.european_option import EuropeanCall, EuropeanPut
from src.quant_finance.instruments.equity.american_option import AmericanCall, AmericanPut
from src.quant_finance.pricers.black_scholes import BlackScholesPricer
from src.quant_finance.pricers.binomial import BinomialPricer


@dataclass
class TestCase:
    name: str
    instrument_type: str          # "EuropeanCall", "EuropeanPut", "AmericanCall", "AmericanPut"
    strike: float
    expiry_days: int
    spot: float
    r: float
    q: float
    sigma: float
    expected_price_range: tuple[float, float] | None = None   # optional sanity check


def load_test_cases() -> List[TestCase]:
    """You can later move this to a yaml file or add more cases here"""
    today = date.today()
    
    return [
        TestCase(
            name="ATM European Call - moderate vol",
            instrument_type="EuropeanCall",
            strike=100.0,
            expiry_days=30,
            spot=100.0,
            r=0.05,
            q=0.02,
            sigma=0.20,
            expected_price_range=(2.8, 3.2)
        ),
        TestCase(
            name="ITM European Put - high vol",
            instrument_type="EuropeanPut",
            strike=110.0,
            expiry_days=60,
            spot=95.0,
            r=0.04,
            q=0.01,
            sigma=0.40,
            expected_price_range=(17.0, 19.0)
        ),
        TestCase(
            name="OTM American Call - low vol",
            instrument_type="AmericanCall",
            strike=120.0,
            expiry_days=45,
            spot=100.0,
            r=0.03,
            q=0.0,
            sigma=0.15
        ),
        TestCase(
            name="Deep ITM American Put - early exercise relevant",
            instrument_type="AmericanPut",
            strike=100.0,
            expiry_days=20,
            spot=80.0,
            r=0.05,
            q=0.0,
            sigma=0.30
        ),
    ]


def run_test_case(test: TestCase) -> None:
    expiry = date.today() + timedelta(days=test.expiry_days)
    
    # Create instrument
    if test.instrument_type == "EuropeanCall":
        instr = EuropeanCall(strike=test.strike, expiry=expiry)
    elif test.instrument_type == "EuropeanPut":
        instr = EuropeanPut(strike=test.strike, expiry=expiry)
    elif test.instrument_type == "AmericanCall":
        instr = AmericanCall(strike=test.strike, expiry=expiry)
    elif test.instrument_type == "AmericanPut":
        instr = AmericanPut(strike=test.strike, expiry=expiry)
    else:
        raise ValueError(f"Unknown instrument type: {test.instrument_type}")

    market = MarketDataSnapshot(
        spot=test.spot,
        risk_free_rate=test.r,
        volatility=test.sigma,
        dividend_yield=test.q,
        valuation_date=date.today()
    )

    # Pricers to compare
    pricers: Dict[str, BasePricer] = {
        "BlackScholes": BlackScholesPricer(),
        "Binomial50": BinomialPricer(n_steps=50),
        "Binomial200": BinomialPricer(n_steps=200),
        "Binomial1000": BinomialPricer(n_steps=1000),  # for convergence check
    }

    print(f"\n{'='*80}")
    print(f"TEST CASE: {test.name}")
    print(f"Instrument: {instr.__class__.__name__} | Strike: {test.strike} | T: {test.expiry_days/365.25:.3f} yr")
    print(f"Market: S={test.spot:.2f}, r={test.r:.3f}, q={test.q:.3f}, σ={test.sigma:.3f}")
    print(f"{'Pricer':12} {'Price':>10} {'Delta':>8} {'Vega':>10} {'Diff vs BS':>12}")
    print("-"*80)

    results = {}
    bs_price = None

    for name, pricer in pricers.items():
        try:
            price = pricer.price(instr, market)
            delta = pricer.delta(instr, market)
            vega  = pricer.vega(instr, market)

            diff = price - bs_price if bs_price is not None else 0.0

            print(f"{name:12} {price:10.4f} {delta:8.4f} {vega:10.4f} {diff:12.4f}")

            results[name] = price

            if name == "BlackScholes":
                bs_price = price

            # Optional sanity check
            if test.expected_price_range and name == "BlackScholes":
                low, high = test.expected_price_range
                if not (low <= price <= high):
                    print(f"  WARNING: BS price {price:.4f} outside expected [{low}, {high}]")

        except Exception as e:
            print(f"{name:12} ERROR: {str(e)}")

    # Quick convergence check for binomial
    if "Binomial50" in results and "Binomial200" in results and "Binomial1000" in results:
        conv_50_200 = abs(results["Binomial50"] - results["Binomial200"])
        conv_200_1000 = abs(results["Binomial200"] - results["Binomial1000"])
        print(f"  Convergence: |50-200| = {conv_50_200:.6f}   |200-1000| = {conv_200_1000:.6f}")


def main():
    parser = argparse.ArgumentParser(description="Run pricing tests and comparisons")
    parser.add_argument("--case", type=int, default=None, help="Run only this test case number (0-based)")
    args = parser.parse_args()

    test_cases = load_test_cases()

    if args.case is not None:
        if 0 <= args.case < len(test_cases):
            run_test_case(test_cases[args.case])
        else:
            print(f"Invalid case number. Available: 0 to {len(test_cases)-1}")
    else:
        for i, case in enumerate(test_cases):
            print(f"\nRunning test case {i}/{len(test_cases)-1}")
            run_test_case(case)


if __name__ == "__main__":
    main()