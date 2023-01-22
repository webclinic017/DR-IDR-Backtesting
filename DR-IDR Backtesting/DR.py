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

    def __init__(self):

        #RDR Vars
        self.rdr_session_vars = {
            'session_name': 'RDR',
            'session_hours': [930, 1030, 1300],   #Var defining start of session, end of session, and end of validity of session
            'dr_high': None,                #Var to store dr high
            'dr_high_timestamp': None,      #dr high timestamp
            'dr_low': None,                 #Var to store dr low
            'dr_low_timestamp': None,       #dr low timestamp
            'idr_high': None,               #Var to store idr high
            'idr_high_timestamp': None,
            'idr_low': None,                #Var to store idr low
            'idr_low_timestamp': None,
            'levelbreaks': [],              #Variable to store all the breaks of relevant levels
            }

        #ODR Vars
        self.odr_session_vars = {
            'session_name': 'ODR',
            'session_hours': [300, 430, 200],
            'dr_high': None,
            'dr_high_timestamp': None,
            'dr_low': None,
            'dr_low_timestamp': None,
            'idr_high': None,
            'idr_high_timestamp': None,
            'idr_low': None,
            'idr_low_timestamp': None,
            'levelbreaks': [],
        }

        #ADR Vars
        self.adr_session_vars = {
            'session_name': 'ADR',
            'session_hours': [1930, 2030, 830],
            'dr_high': None,
            'dr_high_timestamp': None,
            'dr_low': None,
            'dr_low_timestamp': None,
            'idr_high': None,
            'idr_high_timestamp': None,
            'idr_low': None,
            'idr_low_timestamp': None,
            'levelbreaks': [],
        }

        # open a csv file to store the results
        self.csvfile = open('session_results.csv', 'a', newline='') 
        self.csvwriter = csv.writer(self.csvfile)
        self.csvwriter.writerow(['session_name', 'dr_high', 'dr_high_timestamp', 'dr_low', 'dr_low_timestamp', 'idr_high', 'idr_high_timestamp', 'idr_low', 'idr_low_timestamp', 'levelbreaks'])
    
    def next(self):
        print("Reached next()")
        #For every session check if hour has passed or not
        for session_variables in [self.rdr_session_vars, self.odr_session_vars, self.adr_session_vars]:
                hour = int(session_variables['session_hours'][1]) % 12 if int(session_variables['session_hours'][1]) > 12 else int(session_variables['session_hours'][1])
                # Check if the session's defining hour has passed
                if self.data.datetime.time().hour > hour:
                    print("Defining hour has passed")
                    #Check if session is valid
                    if self.data.datetime.time().hour < int(session_variables['session_hours'][2]):
                        print("Session is valid, checking for breaks in any relevant levels")
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
                        #Session is not valid; append variables to csv
                        print("Session is not valid, adding relevant data to csv")
                        self.csvwriter.writerow([session_variables['session_name'], session_variables['dr_high'], session_variables['dr_high_timestamp'], session_variables['dr_low'], session_variables['dr_low_timestamp'], session_variables['idr_high'], session_variables['idr_high_timestamp'], session_variables['idr_low'], session_variables['idr_low_timestamp'], session_variables['levelbreaks']])
                        self.csvfile.flush()

                else:
                    print("Defining hour is ongoing; update prices")
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