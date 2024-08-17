import datetime
import os

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from stock import Stock


class Visualiser():
    def __init__(self, stock):
        
        self.stock = stock
        
        

    def plot_hist(self, field='close', bins=100):
        """
        Plots histogram for a given <field> in the dataframe

        Args:
            field (str, optional): Numeric field present in the dataframe. Defaults to 'close'.
        """
        
        # Core dataframe of the stock
        df = self.stock.data
        # Create histogram data
        hist_data = df[field]
        
        # Create histogram trace
        hist_trace = go.Histogram(x=hist_data, nbinsx=bins, marker=dict(color='rgb(231, 63, 75)', opacity=1))

        # Create layout
        layout = go.Layout(

            bargap=0.025,  # reduce gap between bars
            bargroupgap=0.1,  # increase gap between groups of bars

            title_font=dict(size=30, family='Arial', color='black'),  # set title font
            title=f'Histogram of {self.stock.symbol} : {field}',
            
            xaxis=dict(title=f'{field} value', showgrid=True, gridcolor='black', gridwidth=1),
            yaxis=dict(title='Frequency', showgrid=True, gridcolor='black', gridwidth=1),
            
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='white',
            
            height=600,  # specify height
            width=1200,   # specify width
        )

        # Create figure
        fig = go.Figure(data=[hist_trace], layout=layout)

        # Show plot
        fig.show()
    
            
        
    def plot1candle(self, target_datetime):
        """
        Plots a single candle for analysis

        Args:
            target_datetime (pd.Timestamp): The datetime of the candle to be plotted
            
            Example:
                target_datetime1 = pd.Timestamp(year=2015, month=2, day=23, hour=9, minute=26)
                target_datetime = pd.Timestamp(year=2015, month=2, day=23)
            
        """
        
        # Extract id from datetime, filter out the row of that id, Filter out OHLC values
        idx = self.stock.get_datetime_idx(target_datetime)
        data = self.stock.data.iloc[idx]
        o, h, l, c = data.open.values[0], data.high.values[0], data.low.values[0], data.close.values[0]
        
        # Parameter setttings for the rectangle to be plotted
        rang = 'yellowgreen' if c > o else 'crimson'
        xy  =  (-.25, o)
        height = c-o
        range_abs = h-l


        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(2, 5))

        # Create a rectangle patch
        rectangle = patches.Rectangle(xy, width=.5, height=height, 
                                    linewidth=3, edgecolor='black', 
                                    facecolor=rang, zorder=2)

        # Add the rectangle patch to the axis
        ax.add_patch(rectangle)
        ax.plot([0,0],[l,h], color='black', linewidth=2, zorder=1)   # Line(wick) from bottom to top 
        ax.scatter([0,0],[l,h], color='black')                       # Dots at the wicks end   

        # Set x-axis label
        ax.set_xlabel(str(target_datetime))
        # Set axis limits
        ax.set_xlim(-.75, .75)
        ax.set_ylim(l-range_abs/3, h+range_abs/3)
        
        # Add gridlines behind
        ax.set_axisbelow(True)
        # Show gridlines
        ax.grid(True)

        # Show the plot
        plt.show()
        
        
    
    def plot_priceaction(self, start_datetime, end_datetime, figsize=(40, 12)):
        """
        Plots Candle Stick chart of given data from start_datetime to end_datetime

        Args:
            start_datetime (pd.Timestamp): Starting datetime
            end_datetime (pd.Timestamp): End datetime
        
            Example
                start_datetime = pd.Timestamp(year=2016, month=5, day=18, hour=15, minute=1)
                end_datetime = pd.Timestamp(year=2016, month=5, day=20, hour=12, minute=20)
            
            figsize (tuple, optional): (width,height). Defaults to (40, 12)
        """
        
        # Find id in the diven dataframe
        start_idx = self.stock.get_datetime_idx(start_datetime)[0]
        end_idx = self.stock.get_datetime_idx(end_datetime)[0]
        
        # Title to display 
        title = f'{self.stock.symbol} : {str(start_datetime)} ---> {str(end_datetime)}'

        # Filter data to be plotted
        data = self.stock.data.iloc[start_idx : end_idx+1, :]
                
        # Vertical lines at 9:15 [start of the day]        
        vlines_list = []
        for idx in data.index:
            if idx.time() == datetime.time(9, 15):
                vlines_list.append(idx)
                
        # Plot the candlestick chart
        mpf.plot(data,  
                vlines = { 'vlines' : vlines_list, 'alpha':.7, 'colors':'gold', 'linewidths':5} , 
                type='candle', style='yahoo', title=title, volume=True,
                linecolor='black', figsize = figsize)
                        
        
        
    def plot2candles(self, target_datetime1, target_datetime2):
        """
        Plot two candles side-by-side for comparision
        The plots are such that the height of canvas is same for two candles.
        This helps in analysing the relative size of the candles

        Args:
            target_datetime1 (pd.Timestamp): datetime of the first candle
            target_datetime2 (pd.Timestamp): datetime of the second candle
            
            Example:
                target_datetime1 = pd.Timestamp(year=2016, month=5, day=19, hour=10, minute=15)
                target_datetime2 = pd.Timestamp(year=2021, month=3, day=16, hour=9, minute=20)

        """
        
        # Create subplots with 1 row and 2 columns, Width: 4 inches, Height: 5 inches
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(4, 5), sharey=False)  

        
        # Data and parameters of the 1st candle
        idx1 = self.stock.get_datetime_idx(target_datetime1)
        data1 = self.stock.data.iloc[idx1]
        o1, h1, l1, c1 = data1.open.values[0], data1.high.values[0], data1.low.values[0], data1.close.values[0]
        center1 = (h1 + l1)/2
        
        rang1 = 'yellowgreen' if c1 > o1 else 'crimson'
        xy1  =  (-.25, o1)
        height1 = c1-o1
        range_abs1 = h1-l1 
        
        # Data and parameters of the 1st candle
        idx2 = self.stock.get_datetime_idx(target_datetime2)
        data2 = self.stock.data.iloc[idx2]
        o2, h2, l2, c2 = data2.open.values[0], data2.high.values[0], data2.low.values[0], data2.close.values[0]
        center2 = (h2 + l2)/2
        
        
        rang2 = 'yellowgreen' if c2 > o2 else 'crimson'
        xy2  =  (-.25, o2)
        height2 = c2-o2
        range_abs2 = h2-l2 
        
        # Choose max range from both
        range_abs = max(range_abs1, range_abs2)
        
        
        
        # PLOTTING FIRST CANDLE
        # Create a rectangle patch
        rectangle1 = patches.Rectangle(xy1, width=.5, height=height1, 
                                    linewidth=3, edgecolor='black', 
                                    facecolor=rang1, zorder=2)

        # Add the rectangle patch to the axis
        ax1.add_patch(rectangle1)
        ax1.plot([0,0],[l1,h1], color='black', linewidth=2, zorder=1)
        ax1.scatter([0,0],[l1,h1], color='black')

        # Set x-axis label
        ax1.set_xlabel(str(target_datetime1))
        # Set axis limits
        ax1.set_xlim(-.75, .75)
        ax1.set_ylim(center1-range_abs/1.5, center1+range_abs/1.5)
        
        # Add gridlines behind
        ax1.set_axisbelow(True)
        # Show gridlines
        ax1.grid(True)
        
    
            
        # PLOTTING SECOND CANDLE
        # Create a rectangle patch
        rectangle2 = patches.Rectangle(xy2, width=.5, height=height2, 
                                    linewidth=3, edgecolor='black', 
                                    facecolor=rang2, zorder=2)

        # Add the rectangle patch to the axis
        ax2.add_patch(rectangle2)
        ax2.plot([0,0],[l2,h2], color='black', linewidth=2, zorder=1)
        ax2.scatter([0,0],[l2,h2], color='black')

        # Set x-axis label
        ax2.set_xlabel(str(target_datetime1))
        # Set axis limits
        ax2.set_xlim(-.75, .75)
        ax2.set_ylim(center2-range_abs/1.5, center2+range_abs/1.5)
                
        # Add gridlines behind
        ax2.set_axisbelow(True)
        # Show gridlines
        ax2.grid(True)
        
        
        
        # Show the plot
        plt.tight_layout()
        plt.show()