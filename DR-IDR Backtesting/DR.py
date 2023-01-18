from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

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
            dt = dt or self.satas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        
        #RDR Vars
        self.rdr_session_vars = {
            'session': [930, 1030, 1300],   #Var defining start of session, end of session, and end of validity of session
            'hourpassed_flag': False,       #Var to determine if defining hour is still ongoing or if it has passed (if passed = true)
            'dr_high': None,                #Var to store dr high
            'dr_low': None,                 #Var to store dr low
            'idr_high': None,               #Var to store idr high
            'idr_low': None,                #Var to store idr low
            'valid_flag': False,            #Var to determine if session is still valid (Valid = True)
            'ec': None,                     #Var to determine if early confirmation has occured and if its high or low (None=notset 1=earlylow 2=earlyhigh)
            'c': None                       #VVar to determine if confirmation has occured and if its high or low (None=notset 1=confirmedlow 2=confirmedhigh)
            }

        #ODR Vars
        self.odr_session_vars = {
            'session': [300, 430, 200],
            'hourpassed_flag': False, 
            'dr_high': None,
            'dr_low': None,
            'idr_high': None,
            'idr_low': None,
            'valid_flag': False,
            'ec': None,
            'c': None
        }

        #ADR Vars
        self.adr_session_vars = {
            'session': [1930, 2030, 830],
            'hourpassed_flag': False, 
            'dr_high': None,
            'dr_low': None,
            'idr_high': None,
            'idr_low': None,
            'valid_flag': False,
            'ec': None,
            'c': None
        }

        #Variables to be exportet in the determined data
        self.exportdata = {
        'session': None,                    #which session (RDR, ORD, ADR)
        
        'e_dr_high': None,                  #dr high price
        'e_dr_high_timestamp': None,        #dr high timestamp
        'e_dr_low': None,                   #dr low price
        'e_dr_low_timestamp': None,         #dr low timestamp
        'e_idr_high': None,                 #idr high price
        'e_idr_high_timestamp': None,       #idr high timestamp
        'e_idr_low': None,                  #idr low price
        'e_idr_low_timestamp': None,        #idr low timestamp

        'e_ec': None,                       #close price higher or lower than dr
        'e_ec_timestamp': None,             #timestamp when the early confirmation occured
        'e_c': None,                        #close price higher or lower than idr
        'e_c_timestamp': None,              #timestamp when the confirmation occured

        'e_ec_hold': False,                 #Variable showing if early indication held true
        'e_ec_break_timestamp': None,       #Variable showing timestamp when early confirmation broke
        'e_c_hold': False,                  #Variable showing if confirmation held
        'e_c_break_timestamp': None,        #Variable showing timestamp when confirmation broke

        'e_max_sd': None,                   #Variable storing the maximum standard deviation reached
        'e_max_sd_timestamp': None,         #Variable storing the timestamp of when the maximum standard deviation has been hit
        'e_min_sd': None,                   #Variable storing the lowest standard deviation reached
        'e_max_sd_timestamp': None,         #Variable storing the timestamp of when the lowest standard deviation has been hit

        }

        #To keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None
    

    def next(self):

        session_vars = [self.rdr_session_vars, self.odr_session_vars, self.adr_session_vars]

        for session in session_vars:
            if session['hourpassed_flag'] == False:
                # Check if the session's defining hour has passed
                if self.data.datetime.time() > datetime.time(self.session['session'[1]]):
                    # Update flag if it has
                    self.session['hourpassed_flag'] = True
                else:
                    #update prices if session's defining hour is still ongoing
                    #update dr's
                    if self.data.close[0] > self.session['dr_high']:
                        self.session['dr_high'] = self.data.close[0]
                    if self.data.close[0] < self.session['dr_low']:
                        self.session['dr_low'] = self.data.close[0]
                    
                    #update idr's
                    if self.data.high[0] > self.session['idr_high']:
                        self.session['idr_high'] = self.data.high[0]
                    if self.data.high[0] > self.session['idr_high']:
                        self.session['idr_high'] = self.data.high[0]

            else:
                #Check if session is valid
                if self.data.datetime.time() < datetime.time(self.session['session'[2]]):
                    #Update valid flag
                    session['valid_flag'] = True
                    #before checking for early confirmation and confirmation check if there has already been an early confirmation
                    if self.session['ec'] == None:
                        #check if price closes higher than the dr
                        if self.data.close[0] > self.session['dr_high']:
                            self.session['ec'] = 2
                            #define variable for the timestamp when early indication high occured
                            self.exportdata['e_ec_timestamp'] = self.data.datetime.time()
                        else:
                            #check if price closes lower than the dr
                            if self.data.close[0] < self.session['dr_low']:
                                self.session['ec'] = 1
                                #define variable for timestamp when early indication low occured
                                self.exportdata['e_ec_timestamp'] = self.data.datetime.time()
                        if self.data.close[0] > self.session['idr_high']:
                            self.session['c'] = 2
                        else:
                            #check if price closes lower than the idr
                            if self.data.close[0] < self.session['idr_low']:
                                self.session['c'] = 1
                    else:
                    
                else:
                    session['valid_flag'] = False
            
            #Check if early confirmation has occured than check if the value has been changed from none to 1 or 2
            if self.session['ec'] != None:
                #Check if early confirmation has occured as a low
                if self.session['ec'] == 1:
                    #Check if early confirmation holds by comparing current price to the idr high
                    if self.data.price[0] > self.session['idr_high']:
                        #If the price is higher than idr high the early confirmation hasnt held and we update the indicating variable to false
                        self.exportdata['e_ec_hold'] = False
                    else:
                        self.exportdata['e_ec_hold'] = True
                else:
                    if self.session['ex'] == 2:
                        if self.data.price[0] < self.session['idr_low']:
                            self.exportdata['e_c_hold'] = False
                        else:
                            self.exportdata['e_ec_hold'] = True

            #Check if confirmation has occured than checking if the value has been changed from none to 1 or 2
            if self.session['c'] != None:
                #Check if confirmation has occured as a low
                if self.session['c'] == 1:
                    #Check if confirmation holds by comparing current price to the idr high
                    if self.data.price[0] > self.session['idr_high']:
                        #If the price is higher than idr high the confirmation hasnt held and we update the indicating variable to false
                        self.exportdata['c_hold'] = False
                    else:
                        self.exportdata['c_hold'] = True
                else:
                    if self.session['c'] == 2:
                        if self.data.price[0] < self.session['idr_low']:
                            self.exportdata['c_hold'] = False
                        else:
                            self.exportdata['c_hold'] = True


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    #Add a strategy
    strats = cerebro.optstrategy(
        DR,)

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

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # Set the commision to 0.1%
    cerebro.broker.setcommission(commission=0.001)

    # Print out the starting conditions
    #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run(maxcpus=1)
    #cerebro.plot()

    # Print out the final result
    #print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())