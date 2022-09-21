import numpy as np
import pandas as pd
import yfinance as yf
import datetime as dt
import ssl
import re
import warnings
import matplotlib.pyplot as plt


def costofdebt(ebit, riskfree, interestpayment):
    if isinstance(riskfree, str) and '%' in riskfree:
        riskfree = float(riskfree.replace('%',""))/100
    try:
        interestcoverage = ebit/interestpayment
    except ZeroDivisionError:
        interestcoverage = 10
    finally:
        default = 0
        if interestcoverage >= 8.5 or interestcoverage == np.nan:
            default = 0.0075
        elif interestcoverage >= 6.5 and interestcoverage < 8.5:
            default = .01
        elif interestcoverage >= 5.5 and interestcoverage < 6.5:
            default = 0.015
        elif interestcoverage >= 4.25 and interestcoverage < 5.5:
            default = 0.018
        elif interestcoverage >= 3 and interestcoverage < 4.25:
            default = 0.02
        elif interestcoverage >= 2.5 and interestcoverage < 3:
            default = 0.0225
        elif interestcoverage >= 2.25 and interestcoverage < 2.5:
            default = 0.0275
        elif interestcoverage >= 2 and interestcoverage < 2.25:
            default = 0.035
        elif interestcoverage >= 1.75 and interestcoverage < 2:
            default = 0.0475
        elif interestcoverage >= 1.5 and interestcoverage < 1.75:
            default = 0.065
        elif interestcoverage >= 1.25 and interestcoverage < 1.5:
            default = 0.080
        elif interestcoverage >= 0.8 and interestcoverage < 1.25:
            default = 0.1
        elif interestcoverage >= 0.65 and interestcoverage < 0.8:
            default = 0.115
        elif interestcoverage >= 0.2 and interestcoverage < 0.65:
            default = 0.127
        elif interestcoverage < 0.2:
            default = 0.15
        return default + riskfree

def costofequity(beta, riskfree, riskprem):
    if isinstance(riskfree, str) and '%' in riskfree:
        riskfree = float(riskfree.replace('%',""))/100
    return riskfree + beta*riskprem

def WACC(totaldebt, totalequity, costequity, costdebt, beta, taxrate=0.21):
    
    wacc = costdebt * (1 - taxrate) * (totaldebt / (totalequity + totaldebt)) + costequity * (totalequity / (totalequity + totaldebt))
    
    return wacc

def OperatingMargin(EBIT, Revenue):
    return round(EBIT/Revenue,3)

def balancesheet(ticker):
    ssl._create_default_https_context = ssl._create_unverified_context
    data = "https://stockrow.com/api/companies/{}/financials.xlsx?dimension=Q&section=Balance%20Sheet&sort=desc".format(ticker)
    balance_original = pd.read_excel(data, engine='openpyxl')
    
    balance = balance_original.T
    new_header = balance.iloc[0]
    balance = balance[1:]
    balance.columns = new_header
    
    balance = balance[['Cash and Short Term Investments', 'Shareholders Equity (Total)', 'Total Debt', 'Shares (Common)']]
    
    return balance
    
def incomestatement(ticker):
    ssl._create_default_https_context = ssl._create_unverified_context
    data = "https://stockrow.com/api/companies/{}/financials.xlsx?dimension=Q&section=Income%20Statement&sort=desc".format(ticker)
    income_original = pd.read_excel(data, engine='openpyxl')
    
    columns = ['Revenue','Operating Income', 'Interest Expense (Operating)',
                          'Non-operating Interest Expenses','Income Tax Provision']
    
    income = income_original.T
    new_header = income.iloc[0]
    income = income[1:]
    income.columns = new_header
    
    for col in columns:
        if col not in income.columns:
            income[col] = 0
    
    income = income[['Revenue','Operating Income', 'Interest Expense (Operating)',
                          'Non-operating Interest Expenses','Income Tax Provision']]
    
    income = income[::-1].rolling(4).sum().dropna(how='all').fillna(0)
    
    income['EBIT Margin'] = np.vectorize(OperatingMargin)(income['Operating Income'], income['Revenue'])
    income['Interest'] = income['Interest Expense (Operating)'] + income['Non-operating Interest Expenses']
    
    growth_rate = income['Revenue'].pct_change(1)
    growth_rate.rename('Revenue YoY Growth', inplace=True)
    average_growth_rate = growth_rate.rolling(3).mean()
    average_growth_rate.rename('Average Revenue Growth', inplace=True)
    average_EBIT = income['EBIT Margin'].rolling(3).mean()
    average_EBIT.rename('Average EBIT Margin', inplace=True)
    
    combined_income = pd.concat([income, growth_rate, average_growth_rate, average_EBIT], axis=1)
    
    return combined_income

def ROIC(totaldebt, totalequity, cash, EBIT, taxrate=0.21):
    return EBIT*(1-taxrate)/(totaldebt + totalequity - cash)

def freecashflow(Revenue, EBITMargin, ROIC, growth, WACC, ltgrowth, time=3, taxrate=0.21):
    if ROIC == 0 or ROIC is np.nan:
        ROIC = 0.1
    if isinstance(ltgrowth, str) and '%' in ltgrowth:
        ltgrowth = float(ltgrowth.replace('%',""))/100
    freecashannuity = ((Revenue*EBITMargin*(1-taxrate) * (1 - growth/ROIC))/(WACC - growth))*(1 - ((1+growth)/(1+WACC))**time)
    terminalvalue = (Revenue*EBITMargin*(1-taxrate) * (1 - growth/ROIC))*(1+growth)**time/(WACC - ltgrowth)
    return freecashannuity + terminalvalue

def financialstatement(ticker, equitydata):
    balance_sheet = balancesheet(ticker)
    income_statement = incomestatement(ticker)
    
    combined_fs = pd.concat([balance_sheet, income_statement], axis=1)
    combined_fs.index.name = 'date'      
    equitydata.index.name = 'date'
    
    combined_fs = pd.merge(combined_fs, equitydata, left_index=True, right_index=True)
    combined_fs.reset_index(inplace=True)
    combined_fs.dropna(inplace=True)
                     
    combined_fs['date_calculation'] = combined_fs['date'].astype(str)
    combined_fs['Beta'] = yf.Ticker(ticker).info['beta']
    
    combined_fs['CostofDebt'] = np.vectorize(costofdebt)(combined_fs['Operating Income'], combined_fs['T.Bond Rate'], combined_fs['Interest'])
    combined_fs['CostofEquity'] = np.vectorize(costofequity)(combined_fs['Beta'], combined_fs['T.Bond Rate'], combined_fs['ERP (T12m)'])
    combined_fs['WACC'] = np.vectorize(WACC)(combined_fs['Total Debt'], combined_fs['Shareholders Equity (Total)'], 
                                             combined_fs['CostofEquity'], combined_fs['CostofDebt'], combined_fs['Beta'])
    
    combined_fs['ROIC'] = np.vectorize(ROIC)(combined_fs['Total Debt'], combined_fs['Shareholders Equity (Total)'],
                                            combined_fs['Cash and Short Term Investments'], combined_fs['Operating Income'])
                     
    combined_fs['freecashflow'] = np.vectorize(freecashflow)(combined_fs['Revenue'], combined_fs['Average EBIT Margin'], 
                                                             combined_fs['ROIC'], combined_fs['Average Revenue Growth'],
                                                            combined_fs['WACC'], combined_fs['T.Bond Rate'])
    

    combined_fs.drop(columns=['date_calculation'], inplace=True)
    
    combined_fs['date'] = combined_fs['date'] + pd.Timedelta(1, unit='D') 
    combined_fs['date'] = combined_fs['date'] + pd.DateOffset(months=1)
    
    combined_fs.set_index('date',inplace=True)
    
    return combined_fs