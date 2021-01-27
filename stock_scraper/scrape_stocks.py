from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import matplotlib.pyplot as plt
import alpha_vantage_api_key
from sqlalchemy import create_engine

API_KEY = alpha_vantage_api_key.alpha_vantage_key
TICKERS = ['AAPL','MSFT']

def pull_intraday_time_series_alpha_vantage(alpha_vantage_api_key, ticker_name, data_interval = '15min'):
    """
    Pull intraday time series data by stock ticker name.
    Args:
        alpha_vantage_api_key: Str. Alpha Vantage API key.
        ticker_name: Str. Ticker name that we want to pull.
        data_interval: String. Desired data interval for the data. Can be '1min', '5min', '15min', '30min', '60min'.
    Outputs:
        data: Dataframe. Time series data, including open, high, low, close, and datetime values.
        metadata: Dataframe. Metadata associated with the time series.
    """
    #Generate Alpha Vantage time series object
    print(f'pulling {ticker_name} stocks...')
    ts = TimeSeries(key = alpha_vantage_api_key, output_format = 'pandas')
    #Retrieve the data for the past sixty days (outputsize = full)
    data, meta_data = ts.get_intraday(ticker_name, outputsize = 'full', interval= data_interval)
    data['date_time'] = data.index
    print(f'pulled {data.shape[0]} stock events')
    return data, meta_data


engine = create_engine('sqlite:///stocks.db')
sqlite_connection = engine.connect()
for ticker in TICKERS:
    ts_data, ts_metadata = pull_intraday_time_series_alpha_vantage(API_KEY, ticker_name=ticker, data_interval='1min')
    ts_data_old = pd.read_sql_table(ticker, sqlite_connection, index_col='date')
    ts_total = pd.concat([ts_data_old, ts_data])
    ts_unique = ts_total.drop_duplicates()
    ts_unique.to_sql(ticker, sqlite_connection, if_exists='replace')

sqlite_connection.close()
