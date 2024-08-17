import pandas as pd


def join_dataframes(df1, df2):
    """
    Joins two dataframe to return the combined dataframe
    It's like the union of two data frames

    Args:
        df1 (pandas dataframe): OHLC dataframe, datetime indexed
        df2 (pandas dataframe): OHLC dataframe, datetime indexed

    Returns:
        df3 (pandas dataframe): OHLC dataframe, datetime indexed
                                df3 contains the data of both frames
    """
    
    # Sort according to datetime index
    df1 =  df1.sort_index()
    df2 =  df2.sort_index()
    
    # Create a new dataframe df3 with all indexes
    df3 = pd.concat([df1, df2]).groupby(level=0).first()

    # Fill missing values with values from the other dataframe
    df3 = df3.combine_first(df1).combine_first(df2)
    
    # Sort the new dataset
    df3 =  df3.sort_index()
    
    return df3