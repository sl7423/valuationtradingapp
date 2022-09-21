import numpy as np
import pandas as pd
import yfinance as yf
import datetime as dt
import copy
import ssl
import re
import warnings
import matplotlib.pyplot as plt
from io import StringIO
from .ERP import damodaran_data
from .valuation import financialstatement


def stock_dataframe(tickers, market_ticker='SPY'):
    ohlc_mon = {}
    start = dt.datetime.today() - dt.timedelta(3650)
    end = dt.datetime.today()
    dataframe = pd.DataFrame()
    damodata = damodaran_data()

    for ticker in tickers:
        ohlc_mon[ticker] = yf.download(ticker, start, end, interval='1mo')
        ohlc_mon[ticker].dropna(inplace=True, how='all')
        financial_data = financialstatement(ticker=ticker, equitydata=damodata)
        ohlc_mon[ticker] = ohlc_mon[ticker].merge(financial_data, how='left', left_index=True, right_index=True)
        ohlc_mon[ticker].fillna(method='ffill',inplace=True)
        ohlc_mon[ticker]['Return'] = ohlc_mon[ticker]['Adj Close'].pct_change()
        ohlc_mon[ticker]['Market Capitalization'] = ohlc_mon[ticker]['Shares (Common)'] * ohlc_mon[ticker]['Adj Close']
        ohlc_mon[ticker]['FV Difference Per Share'] = (ohlc_mon[ticker]['freecashflow'] - ohlc_mon[ticker]['Market Capitalization'])/ ohlc_mon[ticker]['Shares (Common)']

    new_ohlc = copy.deepcopy(ohlc_mon)

    for ticker in tickers:
        dataframe[f'{ticker}-return'] = new_ohlc[ticker]['Return']
        dataframe[f'{ticker}-FVDiff'] = new_ohlc[ticker]['FV Difference Per Share']

    dataframe = dataframe.dropna()
    dataframe.reset_index(inplace=True)
    return dataframe


def port(dataframe, m, x):
    portfolio = []
    return_cal = [0]
     
    for i in range(99):
        if len(portfolio) > 0:
            return_cal.append(dataframe[['{}-return'.format(holding) for holding in portfolio]].iloc[i,:].mean())
            sell_selection = dataframe.filter(regex='[A-Za-z]+-FVDiff', axis=1).iloc[i,].sort_values(ascending=True)[:x].index.values.tolist()
            bad_stocks = [re.search('.+?(?=-)', t).group(0) for t in sell_selection]
            portfolio = [t for t in portfolio if t not in bad_stocks]
        fill = m - len(portfolio)
        buy_selection = dataframe.filter(regex='[A-Za-z]+-FVDiff', axis=1).iloc[i,:].sort_values(ascending=False, na_position='last')[:fill].index.values.tolist()
        if len(buy_selection) != 0:
            good_stocks = [re.search('.+?(?=-)', t).group(0) for t in buy_selection]
            portfolio = portfolio + good_stocks
    port_returns = pd.DataFrame(np.array(return_cal), columns=['return'])
    return port_returns

def market(dataframe, ticker='^GSPC'):
    if 'Date' not in dataframe.columns:
        dataframe.reset_index(inplace=True)
    market_df = yf.download('^GSPC', re.search('\d\d\d\d-\d\d-\d\d', str(dataframe.head(1)['Date'].values)).group(0), re.search('\d\d\d\d-\d\d-\d\d', str(dataframe.tail(1)['Date'].values)).group(0), interval='1mo')
    market_df['return'] = market_df['Adj Close'].pct_change().fillna(0)
    return market_df


def yafinance(ticker):
    return_info = {}
    
    ticker_info = yf.Ticker(str(ticker))

    return_info['Name'] = ticker_info.info['shortName']
    return_info['Sector'] = ticker_info.info['sector']
    return_info['PreviousClose'] = ticker_info.info['regularMarketPreviousClose']
    return_info['52WeekHigh'] = ticker_info.info['fiftyTwoWeekHigh']
    return_info['52WeekLow'] = ticker_info.info['fiftyTwoWeekLow']
    return_info['MarketCap'] = ticker_info.info['marketCap']

    return return_info

def return_graph(port_dataframe, market_dataframe):

    fig, ax = plt.subplots()
    plt.plot((1+port_dataframe['return']).cumprod(), label='Portfolio Return')
    plt.plot((1+market_dataframe['return'].reset_index(drop=True)).cumprod(), label='Market Return')
    plt.title("Portfolio Return v. Index Return")
    plt.ylabel("Cumulative Return")
    plt.xlabel("Number of Months")
    plt.legend(loc='best')

    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)

    data = imgdata.getvalue()
    return data

