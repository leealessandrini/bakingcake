import yaml
from marshmallow import Schema, fields, post_load, validates, ValidationError
from . import holding


class PortfolioSchema(Schema):
    """
        Schema for specifying the holding characteristics.
    """
    holdings = fields.List(
        fields.Nested(holding.HoldingSchema), required=True)

    @post_load
    def create_portfolio(self, input_data, **kwargs):
        return Portfolio(**input_data)


class Portfolio(object):
    """
        This class will function as the base object class for a portfolio.
    """

    def __init__(self, holdings):
        """
            Portfolio constructor.
        """
        self.holdings = holdings
        # Get portfolio metrics
        self.portfolio_total = sum([h.total for h in self.holdings])
        self.portfolio_yeild = calculate_portfolio_yield(self.holdings)

        return


# --- Portfolio specific functions ---
def load_portfolio(input_path):
    """
        Load portfolio object provided a file path.

        Args:
            input_path (str): portfolio file input path

        Returns:
            portfolio object
    """
    portfolio_args = yaml.safe_load(open(input_path, "r"))
    """
    portfolio_obj = None
    try:
        portfolio_obj = PortfolioSchema().load(portfolio_args)
    except ValidationError as e:
        print(e)
    """
    portfolio_obj = PortfolioSchema().load(portfolio_args)

    return portfolio_obj


def calculate_portfolio_yield(holdings_list):
    """
        This method will calculate the overall yield of the portfolio.

        Args:
            holdings_list (list): list of portfolio holdings

        Returns:
            portfolio yield
    """
    portfolio_yield = {}
    portfolio_yield["one_year_yield"] = sum(
        [h.annual_yield_usd for h in holdings_list])
    portfolio_yield["one_day_yield"] = (
        portfolio_yield["one_year_yield"] / 365.0)

    return portfolio_yield
