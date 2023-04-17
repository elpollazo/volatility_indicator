from binance.client import Client
import pandas as pd
import numpy as np
import time 
import datetime
import json
from scipy.stats import norm

class DataLoader:
    def __init__(self, pair, delay, read_data_only=False):
        self.pair = pair
        self.delay = delay
        self.retreive_keys()
        self.authenticate()
        self.dataframe = pd.DataFrame()
        self.update_dataframe = pd.DataFrame()
        if not read_data_only:
            self.get_data('5m', '3 day ago')

        self.read_data()
        self.next_date = self.dataframe.index[-1] + 60*5 + 60*self.delay
        self.mu = 0
        self.std = 0
        self.calculate_mu()
        self.calculate_std()

    def retreive_keys(self):
        with open("./keys/binance/api_key", "r") as f:
            api_key = f.read()
            self.api_key = api_key

        with open("./keys/binance/secret_key", "r") as f:
            secret_key = f.read()
            self.secret_key = secret_key

    def authenticate(self):
        print('Authenticating...')
        self.client = Client(self.api_key, self.secret_key)
        print('Good.')

    def fetch_2w_data(self):
        print('Fetching 1m data from 2 weeks ago...')
        for kline in self.client.get_historical_klines_generator(self.pair, '1m', '2 week ago UTC'):
            date = kline[0]
            p_open = float(kline[1])
            p_high = float(kline[2])
            p_low = float(kline[3])
            p_close = float(kline[4])

            #append to dataframe
            row = pd.Series(
                {'date': date, 
                'open': p_open, 
                'high': p_high,
                'low': p_low, 
                'close': p_close
                }
            )

            self.dataframe = pd.concat([self.dataframe, row.to_frame().T])
        
        print('Done')

    def clean_data(self):
        self.dataframe['date'] = self.dataframe['date'] / 1000
        self.dataframe = self.dataframe.set_index('date')
        #self.dataframe = self.dataframe.iloc[:, 1:] #remove first useless column
        
    def update_data(self):
        last_date = self.dataframe.index[-1]
        minutes_ago = str(int((time.time() - last_date + 2*5*60)/60)) #plus 10 min for later union with dataframe
        for kline in self.client.get_historical_klines_generator(self.pair, '5m', '{} minute ago UTC'.format(minutes_ago)):
            date = kline[0]
            p_open = float(kline[1])
            p_high = float(kline[2])
            p_low = float(kline[3])
            p_close = float(kline[4])
            price_change = ((p_high - p_low) / p_low) * 100

            #append to dataframe
            row = pd.Series(
                {'date': date, 
                'open': p_open, 
                'high': p_high,
                'low': p_low, 
                'close': p_close,
                'price_change': price_change,
                'log_price_change': np.log(price_change)
                }
            )

            self.update_dataframe = pd.concat([self.update_dataframe, row.to_frame().T])

        self.update_dataframe['date'] = self.update_dataframe['date'] / 1000
        self.update_dataframe = self.update_dataframe.set_index('date')
        self._merge_dataframes()
        self.dataframe = self.dataframe.iloc[1:] #deleting first row

    def _merge_dataframes(self):
        self.dataframe = self.dataframe.iloc[:-1] #deleting last row
        merge_index = self.dataframe.index[-1]
        self.dataframe = self.dataframe.iloc[:-1] #deleting last row
        self.update_dataframe = self.update_dataframe.loc[merge_index:]
        self.dataframe = pd.concat([self.dataframe, self.update_dataframe])

    """Returns True boolean if data is consistent"""
    def check_data_integrity(self):
        delta = (self.dataframe.index[-1] - self.dataframe.index[0]) / (60 * 5)
        if delta == self.dataframe.shape[0] - 1:
            return True

        else:
            return False

    def save_data(self):
        self.dataframe.to_csv(f'./data/{self.pair}.csv')

    def read_data(self):
        self.dataframe = pd.read_csv(f'./data/{self.pair}.csv')
        self.dataframe['date'] = self.dataframe['date'] / 1000
        self.dataframe = self.dataframe.set_index('date')

    def plus_next_date(self):
        self.next_date = self.dataframe.index[-1] + 60*5 + 60*self.delay

    def get_tickers(self):
        ticker_info = self.client.get_ticker()
        tickers = [ticker['symbol'] for ticker in ticker_info if ticker['symbol'].endswith('USDT')]
        text_chain = '\n'.join(tickers)
        print('Saving tickers in ./data/tickers.txt')
        with open('./data/tickers.txt', 'w') as f:
            f.write(text_chain) 

    def get_data(self, timeframe, long_ago):
        temp_dataframe = pd.DataFrame()
        print('Getting data...')
        for kline in self.client.get_historical_klines_generator(self.pair, timeframe, long_ago + ' UTC'):
            date = kline[0] 
            p_open = float(kline[1])
            p_high = float(kline[2])
            p_low = float(kline[3])
            p_close = float(kline[4])
            price_change = ((p_high - p_low) / p_low) * 100

            #append to dataframe
            row = pd.Series(
                {'date': date, 
                'open': p_open, 
                'high': p_high,
                'low': p_low, 
                'close': p_close,
                'price_change': price_change,
                'log_price_change': np.log(price_change)
                }
            )

            temp_dataframe = pd.concat([temp_dataframe, row.to_frame().T])
        
        temp_dataframe.to_csv(f'./data/{self.pair}.csv')
        print(f'Done. Saved on ./data/{self.pair}.csv')

    def calculate_mu(self):
        self.mu = self.dataframe['log_price_change'].iloc[:-1].mean()

    def calculate_std(self):
        self.std = self.dataframe['log_price_change'].iloc[:-1].std()

    def get_probability(self, value):
        return (1- norm.cdf(value, loc=self.mu, scale=self.std)) 

    @staticmethod
    def to_datetime(date):
        return datetime.datetime.fromtimestamp(date).strftime('%A, %B %-d, %Y %H:%M:%S')