## import packages, init

import pandas as pd
import numpy as np
import requests
import time
import smtplib 
from datetime import datetime
import signal
import logging
logging.basicConfig(filename='app2.log', filemode='a',
                    format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.root.setLevel('INFO')

# get secret variables
from passwords import EMAIL_FROM, PASSWORD, EMAIL_TO


## Define functions 

def get_pi_data(maxtries=5):
    '''
    Queries PI data, returns df object.
    '''
    url = 'https://www.predictit.org/api/marketdata/all/'
    
    t = 0
    while t <= maxtries:
        t += 1
        res = requests.get(url)
        if(res.status_code != 200):
            for i in range(15):
                time.sleep(1)
            continue
        else:
            try:
                df = pd.DataFrame.from_dict(res.json()['markets'])
                return df[['id', 'shortName', 'url']]
            except:
                for i in range(15):
                    time.sleep(1)
                continue
    
    # When PI undergoes maintenance, may be unable to fetch data for a few hours.
    logging.warning('get_pi_data() exceeded maxtries and no data found. Trying again in 15 minutes.')
    for i in range(15*60):
        time.sleep(1)
    return get_pi_data()


def init_email(email=EMAIL_FROM, pw=PASSWORD, maxtries=5):
    '''
    Connects to email, ready to send
    '''
    tries = 0
    
    while tries < maxtries:
        try:
            # initialize
            s = smtplib.SMTP('smtp.gmail.com', 587) 
            s.starttls() 

            # get address and pw
            if not email and not pw:
                email = input('Email? ')
                pw = input('Pw? ')

            # login
            s.login(email, pw)

            return s

        except:
            tries += 1
            logging.warning('Unable to log into email. Trying again # {}.'.format(tries))
            for i in range(5*60):
                time.sleep(1)
            continue
                
    logging.critical('Unable to login to email. Aborting.')
    return 'stop'


def check_new_markets(email_from=EMAIL_FROM, pw=PASSWORD, email_to=EMAIL_TO, api_rate=60, debug=False):
    '''
    Gets list of existing markets, then gets new markets, then sees if anything is new.
    If so, sends email alert with link to market and updates `markets.csv` with id,
    market description, link, and time discovered.
    
    Params:
    -------
    api_rate: int, seconds between API calls. Must be >= 60 per PI policy (they update 
              data every minute)
    
    debug:    bool, set True to have the function add a row to the CSV even if no new 
              markets found, then abort.
    '''
    
    assert all([isinstance(x, str) for x in [email_from, pw, email_to]])
    assert isinstance(api_rate, int) and api_rate >= 60
    assert isinstance(debug, bool)
    pass
    
    df = pd.read_csv('markets.csv')
    idlist = [x for x in df.id.unique()]
    
    while True:
        

        # API request
        try:
            dfres = get_pi_data()
        except:
            logging.warning('Cannot get PI data. Retrying in 15 mins')
            for i in range(15*60):
                time.sleep(1)
            return check_new_markets(pw)
        
        # any new 
        if any(~dfres.id.isin(idlist)) or debug:
            
            # get subset with new markets
            dfsub = dfres.loc[~dfres.id.isin(idlist), :].copy()
            logging.info('Found {} new markets.'.format(len(dfsub)))
            if (len(dfsub) == 0) and debug:
                dfsub = dfres.loc[dfres.index == dfres.index.max(), :].copy()
            dfsub['datedetected'] = datetime.now()
            
            ## send email
            
            # sign in to email
            s = init_email(email_from, pw)
            # stop outer loop if init_email() fails. This would kill the script.
            if s == 'stop':
                break
            
            # Loop through each new market
            for i in dfsub.index:
                
                # prepare message
                msg = '\r\n\r\n'
                url = dfsub.loc[i, 'url']
                url = url[:url.rfind('/')+1]
                msg += dfsub.loc[i, 'shortName'] + ' ' + url
                msg = ''.join(e for e in msg if e.isascii())
                logging.info('New market: ' + msg[4:])
                msg = msg.encode('utf-8')
                
                # send the message
                try:
                    s.sendmail(email_from, email_to, msg)
                except:
                    # This would be strange...login succeeded but sending email failed
                    logging.warning('Uh oh, email failed to send...')
                    continue
                    
            # log out of email
            s.close()
            
            # add new markets to markets.csv
            try:
                dfsub.to_csv('markets.csv', mode='a', index=False, header=False)
                logging.info('Added {} new markets to CSV.'.format(len(dfsub)))
            except:
                # This would be strange...most likely culprit is CSV is open and read-only
                logging.critical('Could NOT add new markets to CSV. Aborting.')
                break
            
            # stop loop if debug
            if debug:
                logging.info('Debug run complete')
                break
                
            # add to idlist
            idlist += [x for x in dfsub.id.unique()]
                
            # completed all steps for new markets
            logging.info('Continuing awaiting new markets...')
                
        # wait a minute and pull API again
        for i in range(api_rate):
            time.sleep(1)
        continue
            
    # Message if loop stops
    logging.critical('check_predictit.py aborted.')


## launch check_new_markets

# send text that process has started
s = init_email()
s.sendmail(EMAIL_FROM, EMAIL_TO, 'predictit.py started!')
s.close()
logging.info('Starting program...')
    
# run function
check_new_markets()
