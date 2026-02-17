# 00_hello_quant.py
import yfinance as yf
import pandas as pd

ticker = "AAPL"
data = yf.download(ticker, period="1mo")
print(data.tail())

# Quick stats
returns = data['Close'].pct_change().dropna()
print(f"Mean daily return: {returns.mean():.4f}")
print(f"Volatility (std):   {returns.std():.4f}")