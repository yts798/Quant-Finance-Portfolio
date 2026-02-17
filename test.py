# 00_hello_quant.py
import yfinance as yf
import pandas as pd

ticker = "AAPL"
data = yf.download(ticker, period="1mo")
print(data.tail())
