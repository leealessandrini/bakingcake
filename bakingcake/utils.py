import datetime
import yaml
import numpy as np
import pandas as pd
from pycoingecko import CoinGeckoAPI


# Initialize
CG_API = CoinGeckoAPI()
# Get the coin list
COIN_LIST = CG_API.get_coins_list()


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


def get_advanced_info(ticker_list):
    """
    This method will get advanced info provided a ticket list.

    Args:
        ticker_list (list): list of tickers

    Returns:
        advanced information DataFrame
    """
    advanced_info_df = pd.DataFrame()
    # Iterate over each ticker and add information to the DataFrame
    for ticker in ticker_list:
        stock_instance = Stock(ticker)
        adv_stats = stock_instance.get_advanced_stats()
        # Coerce object columns to numeric
        adv_stats = adv_stats.apply(pd.to_numeric, errors='coerce') 
        adv_stats["ticker"] = ticker
        advanced_info_df = advanced_info_df.append(
            adv_stats, ignore_index=True)

    return advanced_info_df


def get_price_history_matrix(price_action_df):
    """
        This method will pivot long price data to a price history matrix.

        Args:
            price_action_df (pandas.DataFrame):

        Returns:
            price history matrix
    """
    return price_action_df.pivot(
        index="date", columns="ticker", values="close"
    ).reset_index().set_index("date")


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
    start = pd.Timestamp(price_action_df["date"].min())
    end = pd.Timestamp(price_action_df["date"].max())
    vol_df["start"] = start
    vol_df["end"] = end
    opening_prices = price_action_df.loc[ 
        price_action_df["date"] == start, ["ticker", "open"]]
    closing_prices = price_action_df.loc[
        price_action_df["date"] == end, ["ticker", "close"]]
    vol_df = vol_df.join(opening_prices.set_index("ticker"), on=["ticker"]) 
    vol_df = vol_df.join(closing_prices.set_index("ticker"), on=["ticker"])
    # Calculate overall return
    vol_df["return"] = (vol_df["close"] - vol_df["open"]) / vol_df["open"]
    # Drop count and reset index
    vol_df = vol_df.drop("count", axis=1).reset_index()

    return vol_df


def calculate_delta(df, kpi, period="annual"):
    """
        This method will calculate the growth rate given a financial statement
        and a key performance indicator.

        Args:
            df (pandas.DataFrame): financial statement
            kpi (str): key performance indicator

        Returns:
            growth rate
    """
    latest = 0
    if period == "annual":
        previous = 1
    elif period == "quarterly":
        previous = 4
    growth_rate = (
        (df.iloc[latest][kpi] - df.iloc[previous][kpi]) /
        df.iloc[previous][kpi]) * 100.0

    return growth_rate


def generate_delta_df(ticker_list):
    """
        This method will collect YoY and QoQ delta metrics.

        Args:
            ticker_list (list): list of tickers

        Returns:
            delta DataFrame
    """
    delta_df = pd.DataFrame()
    for ticker in ticker_list:
        print(ticker)
        stock_instance = Stock(ticker)
        # Grab last 2 annual income statements
        ann_inc = stock_instance.get_income_statement(
            period="annual", last=2)
        qt_inc = stock_instance.get_income_statement(
            period="quarterly", last=5)
        row = pd.DataFrame({
            "ticker": [ticker],
            "yoy_rev_delta": [calculate_delta(ann_inc, "totalRevenue")],
            "yoy_opex_delta": [calculate_delta(ann_inc, "operatingExpense")],
            "yoy_ni_delta": [calculate_delta(ann_inc, "netIncome")],
            "yoy_cor_delta": [calculate_delta(ann_inc, "costOfRevenue")],
            "yoy_sgna_delta": [calculate_delta(
                ann_inc, "sellingGeneralAndAdmin")],
            "qoq_rev_delta": [calculate_delta(
                qt_inc, "totalRevenue", period="quarterly")],
            "qoq_opex_delta": [calculate_delta(
                qt_inc, "operatingExpense", period="quarterly")],
            "qoq_ni_delta": [calculate_delta(
                qt_inc, "netIncome", period="quarterly")],
            "qoq_cor_delta": [calculate_delta(
                qt_inc, "costOfRevenue", period="quarterly")],
            "qoq_sgna_delta": [calculate_delta(
                qt_inc, "sellingGeneralAndAdmin", period="quarterly")]})
        # Append row to delta df 
        delta_df = delta_df.append(row, ignore_index=True)

    return delta_df


def calculate_apy(apr, n=365):
    """
        This method will calculate apy given apr and n.

        Args:
            apr (float): Annual percentage rate
            n (int_float): number of compounding periods per year

        Returns:
            Annual percentage yield
    """
    return np.power((1 + (apr / n)), n) - 1


def calculate_apr(apy, n=365):
    """
        This method will calculate apr given apy and n.

        Args:
            apy (float): annual percentage yield
            n (int|float): number of compounding periods per year

        Returns:
            Annual percentage rate
    """
    return n * (np.power(apy + 1, 1 / n) - 1)


def get_token_info(ticker):
    """
        Get the information provided a token's ticker.

        Args:
            ticker (str): ticker symbol as a string

        Return:
            ticker information
    """
    success = False
    token_info = {}
    token_list = [i for i in COIN_LIST if ticker.lower() == i["symbol"]]
    if token_list:
        success = True
        if len(token_list) == 1:
            token_info = token_list[0]
        else:
            i = 0
            while True:
                token_info = token_list[i]
                if (
                    "governance" not in token_info["id"] and
                    "-" in token_info["id"]
                ):
                    i += 1
                else:
                    break

    return token_info, success
