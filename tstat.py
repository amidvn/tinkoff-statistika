import sys
from datetime import datetime, timedelta, time
from decimal import Decimal

from settings import TOKEN, NUMBER_FOR_TOP
from utils import OutputTable

from pytz import timezone, utc
from pycbrf.toolbox import ExchangeRates
from tinkoff.invest import (
    Client,
    GetOperationsByCursorRequest,
    OperationType,
    OperationState,
    MoneyValue
)
from tinkoff.invest.utils import quotation_to_decimal


mapping_figi = dict()
positions = dict()


def get_now() -> datetime:
    moscow_tz = timezone('Europe/Moscow')
    return moscow_tz.localize(datetime.now())


def get_rates(date, dict_rates):
    if date not in dict_rates:
        dict_rates[date] = ExchangeRates(date)
    return dict_rates[date]


def sort_dict(d) -> str:
    list_d = list(d.items())
    list_d.sort(key=lambda i: i[1], reverse=True)
    num = 1
    result = ""
    for figi, value in list_d:
        ticker = mapping_figi.get(figi, figi)
        result += f"{num}) {ticker} (${value:.2f}) "
        num += 1
        if num > NUMBER_FOR_TOP:
            break
    return result


def get_operation_type(op_type: OperationType) -> str:
    if (op_type == OperationType.OPERATION_TYPE_BUY
            or op_type == OperationType.OPERATION_TYPE_BUY_CARD
            or op_type == OperationType.OPERATION_TYPE_BUY_MARGIN):
        return "Buy"
    elif (op_type == OperationType.OPERATION_TYPE_SELL
            or op_type == OperationType.OPERATION_TYPE_SELL_CARD
            or op_type == OperationType.OPERATION_TYPE_SELL_MARGIN):
        return "Sell"
    elif op_type == OperationType.OPERATION_TYPE_MARGIN_FEE:
        return "MarginCommission"
    return ""


def moneyvalue_to_decimal(payment: MoneyValue) -> Decimal:
    fractional = payment.nano / Decimal("10e8")
    return Decimal(payment.units) + fractional


def print_top_results(dict_turnovers, dict_day_profits):
    result_of_sorting = sort_dict(dict_turnovers)
    result_of_sorting_dp = sort_dict(dict_day_profits)
    print(f"ТОП бумаг по обороту: {result_of_sorting}\n"
          f"ТОП бумаг по прибыли: {result_of_sorting_dp}\n")


def day_results(operations, date, date_final, to_reversed, consolidated):
    dict_rates = dict()

    dict_turnovers = dict()
    dict_day_profits = dict()

    summary_table = OutputTable()

    currentdate = date.combine(date.date(), date.min.time())
    table_trades = dict()

    if to_reversed:
        operations.reverse()

    if consolidated:
        period = currentdate.strftime("%Y-%m-%d") + " .. " + date_final.strftime("%Y-%m-%d")
    else:
        period = currentdate

    for operation in operations:
        operation_type = get_operation_type(operation.type)
        if operation_type == "":
            continue
        if operation.state != OperationState.OPERATION_STATE_EXECUTED:
            continue

        operationdate = operation.date - timedelta(hours=3)
        operationdate = operationdate.combine(operationdate.date(), operationdate.min.time())
        if not consolidated:
            period = operationdate
        rates = get_rates(operationdate, dict_rates)

        if operation_type == 'MarginCommission':
            margin = float(abs(quotation_to_decimal(operation.payment)))
            rate_for_usd = 1.0 / float(rates['USD'].value)
            margin_usd = float(margin * rate_for_usd)
            summary_table.set_value(period, "margin", margin)
            summary_table.set_value(period, "margin_usd", margin_usd)
            summary_table.set_value(period, "profit_usd", -margin_usd)
            summary_table.set_value(period, "profit_rub", -margin)

        if operation_type != 'Buy' and operation_type != 'Sell':
            continue

        if not consolidated and operationdate != currentdate:
            table_trades = dict()
            currentdate = operationdate

        summary_table.set_value(period, "num_of_operations", 1)
        payment = abs(quotation_to_decimal(operation.payment))
        currency = operation.payment.currency.upper()
        if currency == 'RUB':
            rate_for_rub = 1
            rate_for_usd = Decimal(1) / Decimal(rates['USD'].value)
        elif currency == 'USD':
            rate_for_rub = Decimal(rates['USD'].value)
            rate_for_usd = 1
        else:
            rate_for_rub = rates[currency].value
            rate_for_usd = Decimal(1) / Decimal(rates['USD'].value) * Decimal(rates[currency].value)

        summary_table.set_value(period, "turnover_usd", float(payment * rate_for_usd))
        summary_table.set_value(period, "turnover_rub", float(payment * rate_for_rub))

        commission = abs(quotation_to_decimal(operation.commission))
        summary_table.set_value(period, "commission_usd", float(commission * rate_for_usd))
        summary_table.set_value(period, "commission_rub", float(commission * rate_for_rub))

        figi = operation.figi

        if figi not in dict_turnovers:
            dict_turnovers[figi] = payment * rate_for_usd
        else:
            dict_turnovers[figi] += payment * rate_for_usd

        quantity = operation.quantity_done if operation_type == 'Buy' else -operation.quantity_done
        if figi in positions:
            positions[figi] -= quantity
            if positions[figi] == 0:
                del positions[figi]
            continue
        if figi not in table_trades:
            direction = 'long' if operation_type == 'Buy' else 'short'
            table_trades[figi] = {'quantity': 0, 'direction': direction, 'buy': 0, 'sell': 0, 'commission': 0, 'currency': currency}
        table_trades[figi]['quantity'] += quantity
        table_trades[figi]['commission'] += Decimal(commission)
        if operation_type == 'Buy':
            table_trades[figi]['buy'] += payment
        elif operation_type == 'Sell':
            table_trades[figi]['sell'] += payment
        if table_trades[figi]['quantity'] == 0:
            profit_day = table_trades[figi]['sell'] - table_trades[figi]['buy'] - table_trades[figi]['commission']
            turnover_deal = table_trades[figi]['sell'] + table_trades[figi]['buy']
            if figi not in dict_day_profits:
                dict_day_profits[figi] = profit_day * rate_for_usd
            else:
                dict_day_profits[figi] += profit_day * rate_for_usd
            del table_trades[figi]
            summary_table.set_value(period, "num_of_trades", 1)
            summary_table.set_value(period, "turnover_intraday", float(turnover_deal * rate_for_usd))
            summary_table.set_value(period, "profit_usd", float(profit_day * rate_for_usd))
            summary_table.set_value(period, "profit_rub", float(profit_day * rate_for_rub))

    print(summary_table)

    print_top_results(dict_turnovers, dict_day_profits)


def get_date_from_string(date_str):
    if len(date_str) != 10:
        return None
    if date_str[6:8] == "20":
        format_date = '%d' + date_str[2] + '%m' + date_str[5] + '%Y'
    elif date_str[0:2] == "20":
        format_date = '%Y' + date_str[4] + '%m' + date_str[7] + '%d'
    else:
        return None
    date_without_sec = datetime.strptime(date_str, format_date).date()
    return datetime.combine(date_without_sec, time(2, 0), tzinfo=utc)


def get_period(args):
    first_date = None
    second_date = None
    date1 = None
    date2 = None
    to_reversed = True
    st_period = None
    standard_periods = ["today", "yesterday", "thisweek", "thismonth", "thisyear", "lastweek", "lastmonth", "lastyear"]

    today = datetime.utcnow().replace(hour=3, minute=0, second=0, microsecond=0)
    today_end = today.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1, microseconds=-1)
    for arg in args:
        date_from_string = get_date_from_string(arg)
        if arg == "from":
            second_date = today
            date2 = today.replace(tzinfo=utc)
        elif date_from_string is not None:
            if first_date is None:
                first_date = date_from_string
                date1 = date_from_string
            elif second_date is None:
                second_date = date_from_string
                date2 = date_from_string
        elif st_period is None and arg.lower() in standard_periods:
            first_date = arg.lower()
            st_period = arg.lower()

    if first_date is None or st_period == "today":
        date1 = today
        date2 = today_end
        to_reversed = False
    elif st_period == "yesterday":
        date1 = today - timedelta(days=1)
    elif st_period == "thisweek":
        date2 = today_end
        weekday = date2.weekday()
        date1 = today - timedelta(days=weekday)
    elif st_period == "thismonth":
        date2 = today_end
        date1 = today.replace(day=1, hour=3, minute=0, second=0, microsecond=0)
    elif st_period == "thisyear":
        date2 = today_end
        date1 = today.replace(month=1, day=1, hour=3, minute=0, second=0, microsecond=0)
    elif st_period == "lastweek":
        weekday = today.weekday()
        date1 = (today - timedelta(days=weekday+7)).replace(hour=3, minute=0, second=0, microsecond=0)
        date2 = today - timedelta(days=weekday+1)
    elif st_period == "lastmonth":
        begin_month = today.replace(day=1, hour=3, minute=0, second=0, microsecond=0)
        date2 = begin_month - timedelta(days=1)
        date1 = date2.replace(day=1, hour=3, minute=0, second=0, microsecond=0)
    elif st_period == "lastyear":
        begin_year = today.replace(month=1, day=1, hour=3, minute=0, second=0, microsecond=0)
        date2 = begin_year - timedelta(days=1)
        date1 = date2.replace(month=1, day=1, hour=3, minute=0, second=0, microsecond=0)

    if date2 is not None and date2 < date1:
        date1, date2 = date2, date1

    return date1, date2, to_reversed


def get_request_operations(account_id, date_from, date_to, cursor):
    return GetOperationsByCursorRequest(
        account_id=account_id,
        cursor=cursor,
        from_=date_from,
        to=date_to,
        limit=1000,
    )


if __name__ == "__main__":
    args = list(sys.argv)
    date1, date2, to_reversed = get_period(args)

    consolidated = 'cons' in args
    for arg in args:
        if 'top' in arg:
            number_for_top_str = arg[4:]
            if number_for_top_str == 'all':
                NUMBER_FOR_TOP = 5000
            elif number_for_top_str.isdigit():
                NUMBER_FOR_TOP = int(number_for_top_str)

    with Client(TOKEN) as client:
        accounts = client.users.get_accounts()
        for acc in accounts.accounts:
            id_acc = acc.id
            break

        operations_items = list()
        cursor = ""

        date1_ts = date1.timestamp()
        while True:
            operations = client.operations.get_operations_by_cursor(get_request_operations(id_acc, date1, date2, cursor))
            if len(operations.items) == 0:
                break
            new_items = [item for item in operations.items if item.date.timestamp() >= date1_ts and item.cursor != cursor]
            if len(new_items) == 0:
                break
            operations_items += new_items
            cursor = operations.items[-1].cursor

        if not to_reversed and date2 >= datetime.now():
            portfolio_positions = client.operations.get_portfolio(account_id=id_acc)
            for position in portfolio_positions.positions:
                positions[position.figi] = quotation_to_decimal(position.quantity)

        for instr in client.instruments.shares().instruments:
            mapping_figi[instr.figi] = instr.ticker
        for instr in client.instruments.bonds().instruments:
            mapping_figi[instr.figi] = instr.ticker
        for instr in client.instruments.futures().instruments:
            mapping_figi[instr.figi] = instr.ticker

    day_results(operations_items, date1, date2, to_reversed, consolidated)
