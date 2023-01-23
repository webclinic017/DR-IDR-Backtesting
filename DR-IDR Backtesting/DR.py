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
            'session_name': 'RDR',                          #Var to store the sessions name
            'defining_hour_start': datetime.time(9, 30),    #Var to store time when session's defining hour starts
            'defining_hour_end': datetime.time(10, 30),     #Var to store time when session's defining hour ends
            'session_validity': datetime.time(13, 00),      #Var to store time when session is invalid
            'dr_high': None,                                #Var to store dr high
            'dr_high_timestamp': None,                      #dr high timestamp
            'dr_low': None,                                 #Var to store dr low
            'dr_low_timestamp': None,                       #dr low timestamp
            'idr_high': None,                               #Var to store idr high
            'idr_high_timestamp': None,             
            'idr_low': None,                                #Var to store idr low
            'idr_low_timestamp': None,              
            'levelbreaks': [],                              #Variable to store all the breaks of relevant levels
            }

        #ODR Vars
        self.odr_session_vars = {
            'session_name': 'ODR',
            'defining_hour_start': datetime.time(3, 00),
            'defining_hour_end': datetime.time(4, 30),
            'session_validity': datetime.time(2, 00),
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
            'defining_hour_start': datetime.time(19, 30),
            'defining_hour_end': datetime.time(20, 30),
            'session_validity': datetime.time(8, 30),
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
        current_time = data.datetime.time()

        print("Checking if current_time is in correct format", current_time)
        #For every session check if hour has passed or not
        print("look how output of defining hour end looks like", datetime.time(10, 30))
        for session_variables in [self.rdr_session_vars, self.odr_session_vars, self.adr_session_vars]:
            print("reached for loop")
            print("Print session name that is being checked for iteration of loop: ", session_variables['session_name'])
            print("Check what the sessions timestamp outputs are; dhs, dhe, sv:", session_variables['defining_hour_start'], session_variables['defining_hour_end'], session_variables['session_validity'])
            print("Check if defining hour is still ongoing")
            if (current_time > session_variables['defining_hour_end']) and (current_time <= session_variables['session_validity']):
                print("Defining hour has passed")
                #Check if session is valid
                if (current_time > session_variables['defining_hour_end']) and (current_time <= session_variables['session_validity']):
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
                        open_price, close_price = self.data.open[-1], self.data.close[-1]
                        for level in levels:
                            result = breaklevel(open_price, close_price, level)
                            session_variables['levelbreaks'].append(session_variables, current_time, level, result, open_price, close_price, levels)
                else:
                    #Session is not valid; append variables to csv
                    print("Session is not valid, adding relevant data to csv")
                    print(session_variables['session_name'], session_variables['dr_high'], session_variables['dr_high_timestamp'], session_variables['dr_low'], session_variables['dr_low_timestamp'], session_variables['idr_high'], session_variables['idr_high_timestamp'], session_variables['idr_low'], session_variables['idr_low_timestamp'], session_variables['levelbreaks'])
                    self.csvwriter.writerow([session_variables['session_name'], session_variables['dr_high'], session_variables['dr_high_timestamp'], session_variables['dr_low'], session_variables['dr_low_timestamp'], session_variables['idr_high'], session_variables['idr_high_timestamp'], session_variables['idr_low'], session_variables['idr_low_timestamp'], session_variables['levelbreaks']])
                    self.csvfile.flush()
            else:
                print("Defining hour is ongoing, check again and then update prices")
                if (current_time >= session_variables['defining_hour_start'] and (current_time <= session_variables['defining_hour_end'])):
                    print("update prices2")
                    #update prices if session's defining hour is still ongoing
                    #update dr's
                    #if (a is None) or (a > b):
                    if (session_variables['dr_high'] == None) or (self.data.close[-1] > session_variables['dr_high']):
                        session_variables['dr_high'] = self.data.close[-1]
                    if (session_variables['dr_low'] == None) or (self.data.close[-1] < session_variables['dr_low']):
                        session_variables['dr_low'] = self.data.close[-1]
                    
                    #update idr's
                    if (session_variables['idr_high'] == None) or (self.data.high[-1] > session_variables['idr_high']):
                        session_variables['idr_high'] = self.data.high[-1]
                    if (session_variables['idr_low'] == None) or (self.data.low[-1] > session_variables['idr_low']):
                        session_variables['idr_low'] = self.data.low[-1]

                        print("Updated values: drhigh:", session_variables['dr_high'], "drlow: ", session_variables['dr_low'], "idrhigh: ", session_variables['idr_high'], "idrlow: ", session_variables['idr_low'])

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    #Add a strategy
    #note that I changed the following line to not have a line break and a comma fter "DR" 20.01.2023 09:11
    strats = cerebro.optstrategy(DR)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    #date,time,open,high,low,close,volume(which is always 0)
    datapath = os.path.join(modpath, '.\data\datasampleforruntimereduction.csv')

    # Create a Data Feed
    data = bt.feeds.GenericCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2000, 1, 1),
        # Do not pass values after this date
        todate=datetime.datetime(2022, 12, 31),
       
        dtformat=('%Y.%m.%d'),
        tmformat=('%H:%M'),

        datetime=0,
        time=1,
        open=2,
        high=3,
        low=4,
        close=5,
        volume=6)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Run over everything
    cerebro.run(maxcpus=1)