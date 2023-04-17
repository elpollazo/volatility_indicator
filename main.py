from batchanalyzer import BatchAnalyzer
from dataloader import DataLoader
import time
import requests
import logging
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def send_alert(message):
    token = ''
    chat_id = ''

    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)

def batch_calculation(ba):
    row = ba.get_last_batch_row()
    p = ba.get_probability(row['mean'])
    if p < 0.02:
        logging.info('Volatile session. Sending alert.')
        batch_date = DataLoader.to_datetime(row['batch_date'])
        send_alert(f'Volatile session. date: {batch_date}, p: {round(p*100, 2)}%')

    else:
        logging.info(f'Non volatile session. p: {round(p*100, 2)}%')

    ba.concat_row(row)

def data_feed(data):
    data.update_data()
    data.plus_next_date()
    if data.check_data_integrity():
        data.save_data()

    else:
        exit()

def main(args):
    data = DataLoader(args.pair, args.delay)
    now = time.time()
    logging.info('System initiated')
    while True:
        if now > data.next_date:
            data.update_data()
            data.plus_next_date()
            if not data.check_data_integrity():
                exit()

            p = data.get_probability(data.dataframe['log_price_change'].iloc[-2])
            if p < 0.02:
                logging.info('Volatile session. Sending alert.')
                volatility_date = DataLoader.to_datetime(data.dataframe.index[-2])
                send_alert(f'Volatile session. date: {volatility_date}, p: {round(p*100, 2)}%')

            else:
                logging.info(f'Non volatile session. p: {round(p*100, 2)}%')

            data.calculate_mu()
            data.calculate_std()

        else:
            time.sleep(1)

        now = time.time()
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pair', 
        help='Cryptocurrency pair to analize',
    	type=str
    )
    parser.add_argument('delay', 
        help='Cryptocurrency pair to analize',
    	type=int
    )
    args = parser.parse_args()
    main(args)