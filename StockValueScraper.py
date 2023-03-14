from requests_html import HTMLSession
#import lxml
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm
import argparse
from tabulate import tabulate
import warnings
import re

from fundamentus import Fundamentus

HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"}

class StockValueScraper:

    def __init__(self, dfFundamentus: pd.DataFrame) -> None:
        self.__dfFundamentus = dfFundamentus

    def __scrap(self) -> None:
        htmlSession = HTMLSession()

        dfFin = pd.DataFrame()

        for tck in tqdm(self.__dfFundamentus['ticker']):
            url = htmlSession.get(f'https://br.financas.yahoo.com/quote/{tck}.SA')
            soup = BeautifulSoup(url.text, 'lxml')
            
            soupTag_price = soup.find('fin-streamer', attrs={'data-symbol':f"{tck}.SA", "data-test":"qsp-price", "data-field":"regularMarketPrice"})
            soupTag_price = float(soupTag_price.get('value'))
            
            soupTag_percent = soup.find('fin-streamer', attrs={'data-symbol':f"{tck}.SA", "data-field":"regularMarketChangePercent"})
            soupTag_percent = float(soupTag_percent.get('value'))
        
            soupTag_limit = soup.find('td', attrs={'data-test':"DIVIDEND_AND_YIELD-value"})
            ssoupTag_limit_value = soupTag_limit.text.split(' ')[0]

            if re.search('^[-+]?\d*\,?\d*$', ssoupTag_limit_value) is not None:
                ssoupTag_limit_value = float(ssoupTag_limit_value.replace(',', '.'))
                ssoupTag_limit_value = float('%.2f' % (ssoupTag_limit_value / 0.06))
            else:
                ssoupTag_limit_value = pd.NA

            dfFin = pd.concat([pd.DataFrame([[ tck, soupTag_price, soupTag_percent, ssoupTag_limit_value ]], columns=('ticker', 'price', 'variation', 'limit')), dfFin], ignore_index=True)
            time.sleep(1)

        return dfFin    

    def process(self) -> None:

        dfFin = self.__scrap()

        dfResult = dfFin.merge(self.__dfFundamentus[['ticker', 'target', 'ranking', 'min', 'max', 'median', 'mean']], how='inner', on='ticker').sort_values(by=['ranking', 'variation'])
        dfResult['% target'] = (dfResult['price'] / dfResult['target']).map("{:.2%}".format)
        dfResult['variation'] = dfResult['variation'].map("{:.2%}".format)
        dfResult = dfResult[['ticker', 'ranking', 'price', 'target', '% target', 'limit', 'min', 'max', 'median', 'mean', 'variation']]
        dfResult.set_index('ticker', inplace=True)

        return dfResult


def main() -> None:

    warnings.simplefilter(action='ignore', category=FutureWarning)

    def arguments() -> argparse.ArgumentParser:
            parser = argparse.ArgumentParser()
            parser.add_argument('-u', '--url', action='store', type=str, required=True, help='URL do site fundamentus')
            parser.add_argument('-dt', '--date', action='store', type=str, required=True, help='Data inicial do histórico das ações')

            args = parser.parse_args()
           
            return args

    args = arguments()

    fundamentus = Fundamentus()
    df = fundamentus.run(args.url, HEADER, args.date)
    
    stocksValue =  StockValueScraper(df)   
    df = stocksValue.process()

    print(tabulate(df, headers='keys', tablefmt='psql'))


if __name__ == '__main__':
    main()