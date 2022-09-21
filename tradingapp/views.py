from django.shortcuts import render, redirect
from .forms import StockForm
from .models import Stock
from django.contrib import messages
from .tradingModels.main import port, market, stock_dataframe, yafinance, return_graph
from .tradingModels.metrics import CAGR, sharpe, max_dd, volatility, convert_percentage


def home(request):
    return render(request, 'home.html')

def add_stock(request):
    if request.method == 'POST':
        form = StockForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Ticker has been entered")
            return redirect('add_stocks')
        else:
            messages.error(request, "Please enter a stock that falls in the index")
            return redirect("add_stocks")
        
    else:
        ticker = Stock.objects.all()
        context = {'tickers': ticker}
        return render(request, 'add_stock.html', context)


def delete(request, stock_id):
    item = Stock.objects.get(pk=stock_id)
    item.delete()
    messages.success(request, "Stock has been deleted")
    return redirect("add_stocks")

def calculateBasicInfo(request):
    ticker = Stock.objects.all()
    stock_info = {}
    for ticker_item in ticker:
        stock_info[ticker_item] = yafinance(ticker_item)
    context = {'tickers': ticker, "stock_infos": stock_info}
    return render(request, 'calculate.html', context)

def output(request):
    tickers = Stock.objects.values_list('ticker',flat=True)
    tickers = list(tickers)

    original_dataframe = stock_dataframe(tickers=tickers)
    combined_dataframe = port(original_dataframe, 2, 1)

    market_dataframe = market(original_dataframe)
    
    port_CAGR = CAGR(combined_dataframe, 'month')
    market_CAGR = CAGR(market_dataframe, 'month')

    port_Vol = volatility(combined_dataframe, 'month')
    market_Vol = volatility(market_dataframe, 'month')

    port_Sharpe = sharpe(port_CAGR, port_Vol, rf=0.02)
    market_Sharpe = sharpe(market_CAGR, market_Vol, rf=0.02)

    port_maxDD = max_dd(combined_dataframe)
    market_maxDD = max_dd(market_dataframe)

    port_CAGR = convert_percentage(port_CAGR)
    market_CAGR = convert_percentage(market_CAGR)
    port_Vol = convert_percentage(port_Vol)
    market_Vol = convert_percentage(market_Vol)
    port_Sharpe = convert_percentage(port_Sharpe)
    market_Sharpe = convert_percentage(market_Sharpe)
    port_maxDD = convert_percentage(port_maxDD)
    market_maxDD = convert_percentage(market_maxDD)

    graph = return_graph(combined_dataframe, market_dataframe)

    context = {'graph': graph, 'portCAGR': port_CAGR, 'marketCAGR': market_CAGR, 'portVol': port_Vol, 'marketVol': market_Vol, 'portSharpe': port_Sharpe, 'marketSharpe': market_Sharpe, 'portMaxDD': port_maxDD, 'marketMaxDD': market_maxDD}
    return render(request, 'output.html', context)