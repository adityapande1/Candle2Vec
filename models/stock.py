import datetime
import math
from collections import OrderedDict
from multiprocessing import Pool

import numpy as np
import pandas as pd


class Stock:
    
    EQUITY_L_PATH = './DATA/EQUITY_L.csv'
    
    df_equity = pd.read_csv(EQUITY_L_PATH) # NSE SYMBOL AND NAME DATASET
    df_equity = df_equity[['SYMBOL', 'NAME OF COMPANY']]
    df_equity = df_equity.rename(columns={'SYMBOL': 'symbol', 'NAME OF COMPANY': 'company_name'})
    
    symbol2name = { symbol : name for symbol, name in zip(df_equity.symbol, df_equity.company_name) }
    
    
    
    def __init__(self, csv_path, remove_incomplete_days=True):
        
        self.csv_path = csv_path    
        self.data = self.read_df(self.csv_path)             # OHLC dataframe
        
        self.total_candles = len(self.data)                 # Num of Candlesticks in the dataset
        self.traded_days = len(set(self.data.index.date))   # Num days market was open
        
        self.cdst_duration_secs = None      # candlestick duration in seconds
        self.cdst_duration_mins = None      # candlestick duration in minutes
        self.cdst_duration_days = None      # candlestick duration in days (None if less than 1 day)
        self._setup_durations()             
        
        self.cdst_per_day =  math.ceil((375*60)/self.cdst_duration_secs)    # candlesticks per day. 1day = 375*60 secs
       
        self.incomplete_day_dates = None            # Num days that dont have full data (375 mins)
        #self._get_incomplete_days(verbose=False)   # This takes time, do not use if incomplete days are already removed        
        
        if remove_incomplete_days:
            
            #print("\nINITIALLY")
            #print(f'TOTAL CANDLES : {self.total_candles} , TOTAL TRADED DAYS : {self.traded_days}\n' )
            self._remove_incomplete_days()
            #print("REMOVED INCOMPLETE DAYS")
            #print(f'TOTAL CANDLES : {self.total_candles} , TOTAL TRADED DAYS : {self.traded_days}\n' )
            
    
        self.symbol = None                  # NSE SYMBOL
        self.company_name = None            
        self._extract_symbol_and_name()
        
      
    def read_df(self, csv_path):
        
        """
        Reads csv file to return dataframe
        dataframe has columns [date, open, high, low, close]
        Args:
            csv_path (str): Path to csv file
        Returns:
            df (pandas Dataframe)
        """
        
        # Read Dataframe
        df = pd.read_csv(csv_path)
        
        # Convert column names to lowercase & select specific cols
        df.columns = df.columns.str.lower()
        
        # Rename the 'timestamp' column to 'date' if it is named such
        if 'timestamp' in list(df.columns):
            df.rename(columns={'timestamp': 'date'}, inplace=True)
        
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        
        # Round open, high, low, close columns to 2 digits
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].round(2)
    
        # Convert the "date" column to datetime & set it as index
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        return df
    

    def trading_day_info(self, target_date):
        """
        Return information about the trading day in a dictionary
        
        Args:
            target_date (datetime.date): date which is to be cheked
                Eg. target_date=datetime.date(2015, 4, 7)
 
        Returns:
            info (Dict): See below, fields are self explainatory
        """
    
        info = {'day_exists'     : False,
                'first_datetime' : None,
                'last_datetime'  : None,
                'num_candles'    : None,
                'is_fullday'     : False,
                }
        
        # The indices where the date part matches the target_date
        matched_indices = self.data.index[self.data.index.date == target_date]
        
        # If there is a match
        if len(matched_indices)>0:
            
            info['day_exists'] = True
            info['first_datetime'] = matched_indices[0]
            info['last_datetime'] = matched_indices[-1]
            info['num_candles'] = len(matched_indices)
            
            # If full day of trading happened
            if (info['last_datetime'] - info['first_datetime']) == datetime.timedelta(hours=6, minutes=14):
                info['is_fullday'] = True
            
        return info
    
    
    def add_additional_features(self):
        
        self.data['ema50'] = self.data['close'].ewm(span=50, adjust=False).mean()

        self.data['center'] = (self.data['open'] + self.data['close'])/2

        self.data['head'] = self.data['high'] -  self.data[['open', 'close']].max(axis=1) 
        self.data['tail'] =  self.data[['open', 'close']].min(axis=1) - self.data['low']
        self.data['body'] = np.abs(self.data['open'] - self.data['close'])
        self.data['range'] = np.abs(self.data['high'] - self.data['low'])

        self.data['head_per_wrt_ema50'] = (self.data['head']/self.data['ema50'])*100
        self.data['tail_per_wrt_ema50'] = (self.data['tail']/self.data['ema50'])*100
        self.data['body_per_wrt_ema50'] = (self.data['body']/self.data['ema50'])*100

        self.data['head_per_wrt_center'] = (self.data['head']/self.data['center'])*100
        self.data['tail_per_wrt_center'] = (self.data['tail']/self.data['center'])*100
        self.data['body_per_wrt_center'] = (self.data['body']/self.data['center'])*100
    
    
    # Function to extract indices for a single target date
    def get_indices(self, target_date):
            
        return self.data.index[self.data.index.date == target_date]


    # Function to chechk if a datetimeindex object is of 375 minutes
    def is_375mins(self, dt_index):
        
        con1 =  dt_index[-1] - dt_index[0] == datetime.timedelta(hours=6, minutes=14)
        con2 = (len(dt_index) == self.cdst_per_day)
        
        return (con1 and con2)
        
    
    def _get_incomplete_days(self, verbose=False):
        """
        Analyses which days traded for less than 6 hrs 15 mins
        Sets a list of incomplete days (trading time != 6hrs 15mins) for the stock
        
        Args:
            verbose (bool, optional): Display the incomplete day dates. Defaults to False.
    
        """
        
        dates_present = list(self.data.index.date)                  # All dates whose data is available
        dates_present = list(OrderedDict.fromkeys(dates_present))   # Unique dates

        # Create a pool of processes
        pool = Pool(processes=50)
        # Apply the function to each target date in parallel
        matched_indices = pool.map(self.get_indices, dates_present)
        # Close the pool
        pool.close()
        pool.join()

        # Create a pool of processes
        pool = Pool(processes=50)
        # Apply the function to each target date in parallel
        fullornot = pool.map(self.is_375mins, matched_indices)
        fullornot = np.array(fullornot)
        # Close the pool
        pool.close()
        pool.join()

        # Filter incomplete day dates
        incomplete_day_dates  = (np.array(dates_present)[~fullornot]).tolist()
        
        if verbose:
            print(incomplete_day_dates)
            
        print(f"\n{len(incomplete_day_dates)}/{self.traded_days} Incomplete days ")

        # Set the attribute self.incomplete_day_dates to the calculated list
        self.incomplete_day_dates = incomplete_day_dates.copy()
    
      
    def get_datetime_idx(self, target_datetime = None):
        """
        Returns the index matching the target_datetime in the self.data dataframe
        
        Args:
            target_datetime (pd.Timestamp): datetime to be matched
                Eg. target_datetime  = pd.Timestamp(2015, 2, 25, 11, 39)

        Returns:
            matched_idx (int)
        """
        
        # If only date is given, It makes the 9:15 as hour:min as default
        if target_datetime.hour==0:
            target_datetime = pd.Timestamp(year=target_datetime.year, month=target_datetime.month, 
                                           day=target_datetime.day, hour=9, minute=15)

        matched_arr =  (self.data.index.tz_localize(None) == target_datetime)
        matched_idx =   np.where(matched_arr)[0]
        # matched_idx =    matched_idx.flatten().tolist()[0]
        
        return matched_idx
    
    
    def _setup_durations(self):
    
        timedelta = self.data.index[1] - self.data.index[0]

        if timedelta.days < 1:

            self.cdst_duration_secs = timedelta.seconds
            self.cdst_duration_mins = self.cdst_duration_secs//60 
            
        else:
            
            self.cdst_duration_days = timedelta.days 
            self.cdst_duration_secs = self.cdst_duration_days * (375*60) 
            self.cdst_duration_mins = self.cdst_duration_secs//60 
            
            
    def _extract_symbol_and_name(self):
        """
        Sets the [self.symbol] and [self.company_name] attributes
        """
                
        # All traded securities symbols
        all_symbols = list(self.symbol2name.keys())
        
        for symbol in all_symbols:    
            if symbol.lower() in self.csv_path.lower():
                
                self.symbol = symbol
                self.company_name = self.symbol2name[symbol]
                
                
    def _remove_incomplete_days(self):
        """
        Removes the incomplete days fron self.data attribute (it's a dataframe)
        """
    
        bad_dates = self.incomplete_day_dates
        filtered_indices = ~np.isin(self.data.index.date, bad_dates)
        
        filtered_df = self.data[filtered_indices]
        
        self.data = filtered_df.copy()
        self.total_candles = len(self.data)                 # Num of Candlesticks in the dataset updated
        self.traded_days = len(set(self.data.index.date))   # Num days market was open updated