import numpy as np
import pandas as pd
import yfinance as yf
import datetime as dt
import copy
import ssl
import re
import warnings


def load_data(path):
    warnings.simplefilter(action='ignore', category=UserWarning)
    return pd.ExcelFile(path)

def damodarandata():
    xls = load_data('https://pages.stern.nyu.edu/~adamodar/pc/implprem/ERPbymonth.xlsx')
    df = pd.read_excel(xls, 'Historical ERP')
    df['Start of month'] = df['Start of month'] - pd.Timedelta(1, unit='D')
    df = df.T
    new_header = df.iloc[0]
    df = df[1:]
    df.columns = new_header
    df = df.T
    df['T.Bond Rate'] = df['T.Bond Rate'].replace({',':'.'}, regex=True)
    return df[['T.Bond Rate','ERP (T12m)']]


def damodaran_data():
    damodata = pd.read_csv(r'./tradingapp/tradingModels/ERP-TBonds.csv')
    damodata['Start of month'] = pd.to_datetime(damodata['Start of month'])
    damodata.set_index('Start of month', inplace=True)
    return damodata

