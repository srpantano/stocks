import pandas as pd
import requests

URL = 'https://www.fundamentus.com.br/resultado.php'
HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"}
DT_START = '2020-12-18'

req = requests.get(URL, headers=HEADER)

dfFundamentusStocks = pd.read_html(req.text, decimal=',', thousands='.')[0]

for col in ['Div.Yield', 'Mrg Ebit', 'Mrg. Líq.', 'ROIC', 'ROE', 'Cresc. Rec.5a']:
    dfFundamentusStocks[col] = dfFundamentusStocks[col].str.replace('.', '')
    dfFundamentusStocks[col] = dfFundamentusStocks[col].str.replace(',', '.')
    dfFundamentusStocks[col] = dfFundamentusStocks[col].str.rstrip('%').astype('float') / 100

dfFundamentusStocks = dfFundamentusStocks[dfFundamentusStocks['Liq.2meses'] > 1000000]

dfFundamentusStocks = dfFundamentusStocks[dfFundamentusStocks['P/L'] <= 12]
dfFundamentusStocks = dfFundamentusStocks[(dfFundamentusStocks['Mrg. Líq.']  * 100) > 10]
dfFundamentusStocks = dfFundamentusStocks[(dfFundamentusStocks['ROE'] * 100) > 15]
dfFundamentusStocks = dfFundamentusStocks[(dfFundamentusStocks['Div.Yield'] * 100) > 6]
dfFundamentusStocks = dfFundamentusStocks[dfFundamentusStocks['Patrim. Líq'] > 100000000.00]
dfFundamentusStocks = dfFundamentusStocks[(dfFundamentusStocks['P/VP'] >= -1) & (dfFundamentusStocks['P/VP'] <= 2)]
dfFundamentusStocks = dfFundamentusStocks[dfFundamentusStocks['EV/EBIT'] > 0]
length_dataframe = dfFundamentusStocks.shape[0] + 1
dfRank = pd.DataFrame()
dfRank['pos'] = range(1, length_dataframe)
dfRank['EV/EBIT'] = dfFundamentusStocks[dfFundamentusStocks['EV/EBIT'] > 0].sort_values(by=['EV/EBIT'])['Papel'].values
dfRank['ROIC'] = dfFundamentusStocks.sort_values(by=['ROIC'], ascending=False)['Papel'].values
dfTemp_a = dfRank.pivot_table(columns='EV/EBIT', values='pos')
dfTemp_b = dfRank.pivot_table(columns='ROIC', values='pos')

sResult = pd.concat([dfRank.pivot_table(columns='EV/EBIT', values='pos'),
          dfRank.pivot_table(columns='ROIC', values='pos')]).dropna(axis=1).sum().sort_values()

dfResult = pd.DataFrame({'ticker': sResult.index, 'ranking': sResult.values})

import yfinance as yf
from datetime import date, timedelta

tickers = ' '.join(list(map(lambda x: x + '.SA', dfResult['ticker'].values.tolist())))
dtEnd = (date.today() - timedelta(1)).strftime('%Y-%m-%d')

dfTickers = yf.download(tickers, start=DT_START, end=dtEnd, actions=True)['Close']

for tkr in dfResult['ticker']:
    dfResult.loc[dfResult['ticker'] == tkr, 'target'] = dfTickers[f'{tkr}.SA'].quantile(.341)
    dfResult.loc[dfResult['ticker'] == tkr, 'max'] = dfTickers[f'{tkr}.SA'].max()
    dfResult.loc[dfResult['ticker'] == tkr, 'mean'] = dfTickers[f'{tkr}.SA'].mean()
    dfResult.loc[dfResult['ticker'] == tkr, 'median'] = dfTickers[f'{tkr}.SA'].median()
    dfResult.loc[dfResult['ticker'] == tkr, 'min'] = dfTickers[f'{tkr}.SA'].min()

dfResult.to_csv('DATA/ranking.csv', index=False)