from requests_html import HTMLSession
import lxml
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm

def read_ranking():
    return pd.read_csv('DATA/ranking.csv')

htmlSession = HTMLSession()

dfFin = pd.DataFrame()

for tck in tqdm(read_ranking()['ticker']):
    url = htmlSession.get(f'https://br.financas.yahoo.com/quote/{tck}.SA')
    soup = BeautifulSoup(url.text, 'lxml')
    
    soupTag_price = soup.find('fin-streamer', attrs={'data-symbol':f"{tck}.SA", "data-test":"qsp-price", "data-field":"regularMarketPrice"})
    soupTag_price = float(soupTag_price.get('value'))
    
    soupTag_percent = soup.find('fin-streamer', attrs={'data-symbol':f"{tck}.SA", "data-field":"regularMarketChangePercent"})
    soupTag_percent = float(soupTag_percent.get('value'))
 
    soupTag_limit = soup.find('td', attrs={'data-test':"DIVIDEND_AND_YIELD-value"})
    soupTag_limit = float(soupTag_limit.text.split(' ')[0].replace(',', '.'))
    soupTag_limit /= 0.06

    dfFin = pd.concat([pd.DataFrame([[ tck, soupTag_price, soupTag_percent, soupTag_limit ]], columns=('ticker', 'price', 'variation', 'limit')), dfFin], ignore_index=True)
    time.sleep(3)
                                       
dfResult = dfFin.merge(read_ranking()[['ticker', 'target', 'ranking', 'min', 'max', 'median', 'mean']], how='inner', on='ticker').sort_values(by=['ranking', 'variation'])
dfResult['% target'] = (dfResult['price'] / dfResult['target']).map("{:.2%}".format)
dfResult['variation'] = dfResult['variation'].map("{:.2%}".format)
dfResult = dfResult[['ticker', 'ranking', 'price', 'target', '% target', 'limit', 'min', 'max', 'median', 'mean', 'variation']]
dfResult.set_index('ticker', inplace=True)

from tabulate import tabulate
print(tabulate(dfResult, headers='keys', tablefmt='psql'))
