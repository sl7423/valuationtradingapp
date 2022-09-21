import pandas as pd
import numpy as np

'''
CAGR, Volatility, and Max Drawdown was inspired from Mayank Rasu's Algorithmms class.

'''


def CAGR(data, interval='monthly'):
    length = 12

    if interval == 'daily':
        length = 365
    elif interval == 'year':
        length = 1
    
    data['cum return'] = (1 + data["return"]).cumprod()
    n = len(data)/length
    
    CAGR = (data['cum return'].tolist()[-1])**(1/n) - 1
    return CAGR


def volatility(data, interval='monthly'):
    length = 12

    if interval == 'daily':
        length = 365
    elif interval == 'year':
        length = 1

    vol = data['return'].std() * np.sqrt(length)
    return vol
    
def sharpe(return_value, risk, rf):
    sharpe = (return_value - rf)/risk
    return sharpe

def convert_percentage(number):
    return "{:.2%}".format(number)


def max_dd(data):
    data['cum return'] = (1 + data['return']).cumprod()
    data['cum roll max'] = data['cum return'].cummax()
    data['drawdown'] = data['cum roll max'] - data['cum return']
    data['drawdown percentage'] = data['drawdown'] / data['cum roll max']
    max_draw = data['drawdown percentage'].max()
    return max_draw