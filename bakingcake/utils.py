import datetime
import pandas as pd
from iexfinance.stocks import Stock
from iexfinance.refdata import get_symbols
from iexfinance.stocks import get_historical_data


def collect_company_index():
    """
        This method will collect an index of all available companies.

        Args:
            None

        Returns:
            company index DataFrame
    """
    type_dict = {
        "ad": "ADR",
        "re": "REIT",
        "ce": "Closed end fund",
        "si":"Secondary Issue",
        "lp": "Limited Partnerships",
        "cs": "Common Stock",
        "et": "ETF",
        "wt": "Warrant",
        "oef": "Open Ended Fund",
        "cef": "Closed Ended Fund",
        "ps": "Preferred Stock",
        "ut": "Unit",
        "temp":"Temporary"}
    symbols = get_symbols(output_format='pandas')
    symbols["type_name"] = symbols["type"].apply(
        lambda x: x if x is None or x == "struct" else type_dict[x])

    return symbols


def get_price_action(
        ticker_list,
        start=datetime.datetime.today() - datetime.timedelta(days=31),
        end=datetime.datetime.today() - datetime.timedelta(days=1)):
    """
        This method will pull the stock price volatility given a list of
        tickers and a start and end date.

        Args:
            ticker_list (list): list of tickers
            start (datetime.datetime): start date
            end (datetime.datetime): end date

        Returns:
            volatility DataFrame
    """
    cols = ["ticker", "open", "close", "low", "high", "changePercent"]
    price_action_df = pd.DataFrame()
    # Iterate over each ticker and add information to the DataFrame
    for ticker in ticker_list:
        df = get_historical_data(ticker, start, end)
        df["ticker"] = ticker
        # Set name of index to date
        df.index = df.index.set_names(['date'])
        # Cast values to floating point numbers
        for column in cols[1:]:
            df[column] = df[column].astype(float)
        price_action_df = price_action_df.append(
            df.loc[:, cols].reset_index(),
            ignore_index=True)

    return price_action_df


def get_volatility(price_action_df):
    """
        This method will get volatility metrics given price action.

        Args:
            price_action_df (pandas.DataFrame): historical price action

        Returns:
            volatility DataFrame
    """
    # Groupby ticker and describe each percent change for each
    vol_df = price_action_df.groupby("ticker")[["changePercent"]].describe()
    low = price_action_df.groupby("ticker")["low"].min()
    high = price_action_df.groupby("ticker")["high"].max()
    # Join column levels
    vol_df.columns = vol_df.columns.levels[1]
    # Add overall low and high prices
    vol_df = vol_df.join(low, on="ticker").join(high, on="ticker")
    # Add latest close as current price
    end = pd.Timestamp(price_action_df["date"].max())
    closing_prices = price_action_df.loc[
        price_action_df["date"] == end, ["ticker", "close"]] 
    vol_df = vol_df.join(closing_prices.set_index("ticker"), on=["ticker"])
    # Drop count and reset index
    vol_df = vol_df.drop("count", axis=1).reset_index()

    return vol_df