import os
import datetime

import tinvest


TOKEN = os.getenv("TINVEST_TOKEN")
client = tinvest.SyncClient(TOKEN)


def get_portfolio() -> list:
    api = tinvest.PortfolioApi(client)
    response = api.portfolio_get()
    positions = response.parse_json().payload.positions
    return positions


def get_portfolio_currencies() -> list:
    api = tinvest.PortfolioApi(client)
    response = api.portfolio_currencies_get()
    positions = response.parse_json().payload.currencies
    return positions


def get_operations(date1, date2) -> list:
    day_begin = date1.replace(hour=2, minute=0, second=0, microsecond=0)
    if date2 is None:
        day_end = day_begin + datetime.timedelta(days=1)
    else:
        day_end = date2.replace(hour=2, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)

    api = tinvest.OperationsApi(client)
    response = api.operations_get(from_=day_begin, to=day_end)
    operations = response.parse_json().payload.operations
    return operations


def get_market_instruments(type_instrument: str) -> list:
    api = tinvest.MarketApi(client)
    if type_instrument.lower() == "stocks":
        response = api.market_stocks_get()
    elif type_instrument.lower() == "bonds":
        response = api.market_bonds_get
    elif type_instrument.lower() == "etfs":
        response = api.market_etfs_get
    elif type_instrument.lower() == "currencies":
        response = api.market_currencies_get
    instruments = response.parse_json().payload.instruments
    return instruments


def get_market_stocks_tickers_from_figi() -> dict:
    instruments = get_market_instruments("stocks")
    D = dict()
    for instrument in instruments:
        D[instrument.figi] = instrument.ticker
    return D


def search_figi(figi):
    api = tinvest.MarketApi(client)
    response = api.market_search_by_figi_get(figi)
    result = response.parse_json().payload
    return result


if __name__ == "__main__":
    pass
