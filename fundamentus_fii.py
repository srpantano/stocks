import pandas as pd
import requests
import yfinance as yf
from datetime import date, timedelta
from tabulate import tabulate

from fundamentus import Fundamentus

#URL = 'https://www.fundamentus.com.br/resultado.php'
HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"}
#DT_START = '2020-12-18'
COLS = {'fundamentus': (
            "FFO Yield", 
            "Dividend Yield", 
            "Cap Rate",
            "Vacância Média"),
        'explorer': (
            "Preço Atual",
            'Dividendo',
            "Dividend Yield",
            "DY (3M) Acumulado",
            "DY (6M) Acumulado",
            "DY (12M) Acumulado",
            "DY (3M) Média",
            "DY (6M) Média",
            "DY (12M) Média",
            "DY Ano",
            "Variação Preço",
            "Rentab. Período",
            "Rentab. Acumulada",
            "Patrimônio Líq.",
            "VPA",
            "DY Patrimonial",
            "Variação Patrimonial",
            "Rentab. Patr. no Período",
            "Rentab. Patr. Acumulada",
            "Vacância Física",
            "Vacância Financeira"
        )}

class FundamentusFII(Fundamentus):

    def _clean_data(self, dfExplorer: pd.DataFrame, dfFundamentus: pd.DataFrame, cols: tuple) -> pd.DataFrame:

        df = dfExplorer.merge(dfFundamentus[['Papel', 'Liquidez']], on='Papel', how='left')
        df.drop(["Liquidez Diária"], axis=1, inplace=True)

        columns = df.columns.tolist()
        newColumns = columns[0:3]
        newColumns.extend(columns[-1:])
        newColumns.extend(columns[-23:])

        df = df[newColumns[:-1]]

        dfFayth = pd.read_csv('jan-fev.csv', sep=';')

        print(dfFayth)

        dfTemp = df.merge(dfFayth, on='Papel', how='left')

        print(tabulate(dfTemp[['Papel', 'Segmento', 'Segment', 'Tipo']], headers='keys', tablefmt='psql'))

        #return super()._clean_data(df, cols)
  
    def _filter(self, df: pd.DataFrame) -> pd.DataFrame:

        dfIFIX = pd.read_csv('IFIXQuad_1-2023.csv', sep=';')

        df = df[df['Papel'].isin(dfIFIX['Papel'])]

        df = df[df['Liquidez'] > 1000000]        

        df = df[(df['Segmento'] == 'Títulos e Val. Mob.') | (df['Segmento'] == 'Outros') | (df['Quantidade Ativos'] >= 3)].sort_values(by='Papel')

        print(df['Segmento'].value_counts())
        print(df[df['Segmento'] == 'Outros'][['Papel', 'Segmento']])

        #dfTitulos = df[df['Segmento'] == "Títulos e Val. Mob."]
        #dfNotTitulos = df[df['Segmento'] != "Títulos e Val. Mob."]

        #print(tabulate(df[df['Liquidez'] > 1000000], headers='keys', tablefmt='psql'))

        #return df

    def __magicFormula(self, df) -> pd.DataFrame:

        length_dataframe = df.shape[0] + 1
        dfRank = pd.DataFrame()
        dfRank['pos'] = range(1, length_dataframe)
        dfRank['EV/EBIT'] = df[df['EV/EBIT'] > 0].sort_values(by=['EV/EBIT'])['Papel'].values
        dfRank['ROIC'] = df.sort_values(by=['ROIC'], ascending=False)['Papel'].values
        #dfTemp_a = dfRank.pivot_table(columns='EV/EBIT', values='pos')
        #dfTemp_b = dfRank.pivot_table(columns='ROIC', values='pos')

        sResult = pd.concat([dfRank.pivot_table(columns='EV/EBIT', values='pos'),
                dfRank.pivot_table(columns='ROIC', values='pos')]).dropna(axis=1).sum().sort_values()

        return pd.DataFrame({'ticker': sResult.index, 'ranking': sResult.values})

    def __downloadValues(self, df) -> pd.DataFrame:

        tickers = ' '.join(list(map(lambda x: x + '.SA', df['ticker'].values.tolist())))
        
        dtEnd = (date.today() - timedelta(1)).strftime('%Y-%m-%d')

        return yf.download(tickers, start=self.__dt_start, end=dtEnd, actions=True, progress=False)['Close']
    
    def __dataProcess(self, dfMF, dfTickers) -> pd.DataFrame:
        
        for tkr in dfMF['ticker']:

            dfMF.loc[dfMF['ticker'] == tkr, 'target'] = dfTickers[f'{tkr}.SA'].quantile(.341)
            dfMF.loc[dfMF['ticker'] == tkr, 'max'] = dfTickers[f'{tkr}.SA'].max()
            dfMF.loc[dfMF['ticker'] == tkr, 'mean'] = dfTickers[f'{tkr}.SA'].mean()
            dfMF.loc[dfMF['ticker'] == tkr, 'median'] = dfTickers[f'{tkr}.SA'].median()
            dfMF.loc[dfMF['ticker'] == tkr, 'min'] = dfTickers[f'{tkr}.SA'].min()

        return dfMF

    def __scrapePage(self, url: str) -> pd.DataFrame:
        df = super()._request_html(url, HEADER)
        
        return df

    def run(self, dt_start: str = '2020-12-18') -> pd.DataFrame:

        dfExplorer = self.__scrapePage('https://www.fundsexplorer.com.br/ranking')
        dfExplorer.rename({"Código do fundo": 'Papel', 'Setor': 'Segmento'}, axis=1, inplace=True)

        dfFundamentus = self.__scrapePage('https://www.fundamentus.com.br/fii_resultado.php')

        df = self._clean_data(dfExplorer, dfFundamentus, COLS['explorer'])

        #df = self._filter(df)
        #dfMagicFormula = self.__magicFormula(dfFundamentus)
        #dfDownloadValues = self.__downloadValues(dfMagicFormula)

        

        #return self.__dataProcess(dfMagicFormula, dfDownloadValues)
    

def main() -> None:

    fundamentusFII = FundamentusFII()
    fundamentusFII.run()
    

if __name__ == '__main__':
    main()    
