import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import datetime
from dataloader import DataLoader
import argparse

def plot_chart(df):
    fig = go.Figure(
        data=[
            go.Candlestick(x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['high'],
            close=df['close']
            )
        ]
    )

    fig.show()

def plot_histogram(df):
    df['log_price_change'].plot.hist(bins=100)
    mu = df['log_price_change'].mean()
    sigma = df['log_price_change'].std()
    plt.axvline(x = mu, color = 'b', label = 'mu')
    plt.axvline(x = mu+sigma, color = 'r', label = 'mu')
    plt.axvline(x = mu+2*sigma, color = 'r', label = 'mu')
    plt.axvline(x = mu+3*sigma, color = 'r', label = 'mu')
    plt.axvline(x = mu-sigma, color = 'r', label = 'mu')
    plt.axvline(x = mu-2*sigma, color = 'r', label = 'mu')
    plt.axvline(x = mu-3*sigma, color = 'r', label = 'mu')

    plt.show()

def main(args):
    df = pd.read_csv(f'./data/{args.file}')
    df['price_change'] = ((df['high'] - df['low']) / df['low']) * 100
    df['log_price_change'] = np.log(df['price_change'])
    if args.type == 'chart':
        plot_chart(df)

    elif args.type == 'histogram':
        plot_histogram(df)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', 
        help='csv file',
    	type=str
    )
    parser.add_argument('type', 
        help='chart type',
    	type=str
    )
    args = parser.parse_args()
    main(args)