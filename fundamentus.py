import pandas as pd
import requests
import yfinance as yf
from datetime import date, timedelta

#URL = 'https://www.fundamentus.com.br/resultado.php'
#HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"}
#DT_START = '2020-12-18'

class Fundamentus:

    def _request_html(self, url, header) -> None: 
        req = requests.get(url, headers=header)
        return pd.read_html(req.text, 
                            decimal=',', 
                            thousands='.', 
                            encoding='utf-8')[0]
    
    def _clean_data(self, df, cols) -> pd.DataFrame:

        for col in cols:     

            text = df[col]

            text = text.str.replace('.', '')
            text = text.str.replace(',', '.')

            currency = "R$ "
            percent = '%'

            if text.loc[text.str.startswith(currency, na=False)].size > 0:
                text = text.str.lstrip(currency).astype('float')
            elif text.loc[text.str.endswith(percent, na=False)].size > 0:
               text = text.str.rstrip(percent).astype('float') / 100

            df[col] = text

        return df

    def _filter(self, df) -> pd.DataFrame:
     
        df = df[df['Liq.2meses'] > 1000000]
        df = df[df['P/L'] <= 12]
        df = df[(df['Mrg. Líq.']  * 100) > 10]
        df = df[(df['ROE'] * 100) > 15]
        df = df[(df['Div.Yield'] * 100) > 6]
        df = df[df['Patrim. Líq'] > 100000000.00]
        df = df[(df['P/VP'] >= -1) & (df['P/VP'] <= 2)]
        df = df[df['EV/EBIT'] > 0]

        return df

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

    def __downloadValues(self, df, dt_start) -> pd.DataFrame:

        tickers = ' '.join(list(map(lambda x: x + '.SA', df['ticker'].values.tolist())))
        
        dtEnd = (date.today() - timedelta(1)).strftime('%Y-%m-%d')

        return yf.download(tickers, start=dt_start, end=dtEnd, actions=True, progress=False)['Close']
    
    def __dataProcess(self, dfMF, dfTickers) -> pd.DataFrame:
        
        for tkr in dfMF['ticker']:

            dfMF.loc[dfMF['ticker'] == tkr, 'target'] = dfTickers[f'{tkr}.SA'].quantile(.341)
            dfMF.loc[dfMF['ticker'] == tkr, 'max'] = dfTickers[f'{tkr}.SA'].max()
            dfMF.loc[dfMF['ticker'] == tkr, 'mean'] = dfTickers[f'{tkr}.SA'].mean()
            dfMF.loc[dfMF['ticker'] == tkr, 'median'] = dfTickers[f'{tkr}.SA'].median()
            dfMF.loc[dfMF['ticker'] == tkr, 'min'] = dfTickers[f'{tkr}.SA'].min()

        return dfMF

    def run(self, url, header, dt_start = '2020-12-18') -> pd.DataFrame:

        df = self._request_html(url, header)
        df = self._clean_data(df, 
                                ('Div.Yield', 
                                 'Mrg Ebit', 
                                 'Mrg. Líq.', 
                                 'ROIC', 
                                 'ROE', 
                                 'Cresc. Rec.5a'))
        df = self._filter(df)
        dfMagicFormula = self.__magicFormula(df)
        dfDownloadValues = self.__downloadValues(dfMagicFormula, dt_start)

        return self.__dataProcess(dfMagicFormula, dfDownloadValues)