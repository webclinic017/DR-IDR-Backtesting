from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import csv
from enum import Enum
import numpy as np
import pandas as pd

# Import the backtrader platform
import backtrader as bt


# Create a Stratey
class DR(bt.Strategy):
    params = (
        ('printlog', False),
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        
        #RDR Vars
        self.rdr_session_vars = {
            'session': [930, 1030, 1300],   #Var defining start of session, end of session, and end of validity of session
            'hourpassed_flag': False,       #Var to determine if defining hour is still ongoing or if it has passed (if passed = true)
            'dr_high': None,                #Var to store dr high
            'dr_high_timestamp': None,      #dr high timestamp
            'dr_low': None,                 #Var to store dr low
            'dr_low_timestamp': None,       #dr low timestamp
            'idr_high': None,               #Var to store idr high
            'idr_high_timestamp': None,
            'idr_low': None,                #Var to store idr low
            'idr_low_timestamp': None,
            'valid_flag': False,            #Var to determine if session is still valid (Valid = True)
            'levelbreaks': [],              #Variable to store all the breaks of relevant levels
            }

        #ODR Vars
        self.odr_session_vars = {
            'session': [300, 430, 200],
            'hourpassed_flag': False, 
            'dr_high': None,
            'dr_high_timestamp': None,
            'dr_low': None,
            'dr_low_timestamp': None,
            'idr_high': None,
            'idr_high_timestamp': None,
            'idr_low': None,
            'odr_low_timestamp': None,
            'valid_flag': False,
            'levelbreaks': [],
        }

        #ADR Vars
        self.adr_session_vars = {
            'session': [1930, 2030, 830],
            'hourpassed_flag': False, 
            'dr_high': None,
            'dr_high_timestamp': None,
            'dr_low': None,
            'dr_low_timestamp': None,
            'idr_high': None,
            'idr_high_timestamp': None,
            'idr_low': None,
            'odr_low_timestamp': None,
            'valid_flag': False,
            'levelbreaks': [],
        }
    
    def next(self):

        for session_variables in [self.rdr_session_vars, self.odr_session_vars, self.adr_session_vars]:
            if session_variables['hourpassed_flag'] == False:
                hour = int(session_variables['session'][1]) % 12 if int(session_variables['session'][1]) > 12 else int(session_variables['session'][1])
                # Check if the session's defining hour has passed
                if self.data.datetime.time().hour > hour:
                    # Update flag if it has
                    session_variables['hourpassed_flag'] = True
                else:
                    #update prices if session's defining hour is still ongoing
                    #update dr's
                    if self.data.close[0] > session_variables['dr_high']:
                        session_variables['dr_high'] = self.data.close[0]
                    if self.data.close[0] < session_variables['dr_low']:
                        session_variables['dr_low'] = self.data.close[0]
                    
                    #update idr's
                    if self.data.high[0] > session_variables['idr_high']:
                        session_variables['idr_high'] = self.data.high[0]
                    if self.data.high[0] > session_variables['idr_high']:
                        session_variables['idr_high'] = self.data.high[0]

            else:
                #Check if session is valid
                if self.data.datetime.time().hour < int(session_variables['session'][2]):
                    #Update valid flag
                    session_variables['valid_flag'] = True
                    #Check for breaks in DR and IDR Levels and store them in list
                    #following code is supposed to be in session loop
                    class breakdirection(Enum):
                        BROKE_BELOW = 1
                        BROKE_ABOVE = 2

                    def breaklevel(open_price, close_price, level):
                        if open_price <= level <= close_price:
                            return breakdirection.BROKE_BELOW
                        elif open_price >= level >= close_price:
                            return breakdirection.BROKE_ABOVE

                        levels = [session_variables['dr_low'], session_variables['idr_low'], session_variables['dr_high'], session_variables['idr_high']]
                        open_price, close_price = self.data.open[0], self.data.close[0]

                        for level in levels:
                            result = breaklevel(open_price, close_price, level)
                            session_variables['levelbreaks'].append(session_variables, self.data.datetime.time(), level, result, open_price, close_price, levels)

                else:
                    session_variables['valid_flag'] = False
                    df = pd.DataFrame.from_dict(session_variables)
                    df.to_csv('session_vars.csv', mode='a', header=False)

            #np.savetxt('data.csv', (session_variables), delimiter=',')

            #df = pd.DataFrame.from_dict(session_variables)
            #df.to_csv("data.csv", index=False)
#           Both, above and below dont make sense first of all because i should probably put the code which exports the data into csv file when the session is over, so in the code above when checking if session is valid
            # Get the length of the first value in the dictionary
            #length = len(next(iter(session_variables.values())))
            #
            ## Iterate through the dictionary and check the length of each value
            #for key, value in session_variables.items():
            #    if len(value) != length:
            #        print(f'{key} has a different length: {len(value)}')

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    #Add a strategy
    #note that I changed the following line to not have a line break and a comma fter "DR" 20.01.2023 09:11
    strats = cerebro.optstrategy(DR)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '.\data\GBPJPY=X.csv')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2000, 1, 1),
        # Do not pass values before this date
        todate=datetime.datetime(2022, 12, 31),
        # Do not pass values after this date
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Run over everything
    cerebro.run(maxcpus=1)