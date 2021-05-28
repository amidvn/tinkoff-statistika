import sys
import datetime
import locale
from decimal import Decimal

from pytz import timezone
from pycbrf.toolbox import ExchangeRates
from prettytable import PrettyTable

import tinkoff


def get_now() -> datetime:
    moscow_tz = timezone('Europe/Moscow')
    return moscow_tz.localize(datetime.datetime.now())


def nft(num):
    return locale.format_string('%0.2f', num, grouping=True)


def print_with_footer(ptable, num_footers=1):
    """ Print a prettytable with an extra delimiter before the last `num` rows """
    lines = ptable.get_string().split("\n")
    hrule = lines[0]
    lines.insert(-(num_footers + 1), hrule)
    print("\n".join(lines))


def calculate_totals(ptable, oborot_summary):
    summary_list = [Decimal('0') for _ in range(8)]
    for row in ptable:
        row.border = False
        row.header = False
        value = row.get_string().strip()
        lst = list(map(Decimal, value.split('  ')[1:]))
        summary_list = [x + y for x, y in zip(summary_list, lst)]
    summary_list = ["TOTAL"] + summary_list
    summary_list[7] = round(summary_list[5] / oborot_summary * 200, 2)
    ptable.add_row(summary_list)


def sort_dict(d) -> str:
    list_d = list(d.items())
    list_d.sort(key=lambda i: i[1], reverse=True)
    num = 1
    result = ""
    for i in list_d:
        figi = i[0]
        value = round(i[1], 2)
        ticker = tinkoff.search_figi(figi).ticker
        result += f"{num}) {ticker} (${value}) "
        num += 1
        if num > 5:
            break
    return result


def print_top_results(dict_turnovers, dict_day_profits):
    result_of_sorting = sort_dict(dict_turnovers)
    result_of_sorting_dp = sort_dict(dict_day_profits)
    print(f"ТОП бумаг по обороту: {result_of_sorting}\n"
          f"ТОП бумаг по прибыли: {result_of_sorting_dp}\n")


def day_results(operations, date, to_reversed, consolidated):
    rates = ExchangeRates(date)
    oborot_rub = Decimal('0')
    oborot_usd = Decimal('0')
    oborot_intraday = Decimal('0')
    oborot_intraday_summary = Decimal('0')
    commission_rub = Decimal('0')
    commission_usd = Decimal('0')
    profit_rub = Decimal('0')
    profit_usd = Decimal('0')
    efficiency = Decimal('0')
    num_of_trades = 0

    if not to_reversed:
        portfolio_positions = tinkoff.get_portfolio()
        positions = dict()
        for position in portfolio_positions:
            positions[position.figi] = position.balance
    else:
        positions = dict()
    table_trades = dict()

    dict_turnovers = dict()
    dict_day_profits = dict()

    summary_table = PrettyTable()
    # summary_table.field_names = ["Day", "Turnover, $", "Turnover, ₽", "Comm., $", "Comm., ₽", "Profit/loss, $", "Profit/loss, ₽", "Efficiency, %", "Amount of trades"]
    summary_table.field_names = ["День", "Оборот, $", "Оборот, ₽", "Комиссия, $", "Комиссия, ₽", "Финрез, $", "Финрез, ₽", "Эфф-сть, %", "Кол-во сделок"]
    summary_table.align = "r"
    summary_table.align["День"] = "c"

    currentdate = date.combine(date.date(), date.min.time())
    startdate = currentdate

    if to_reversed:
        operations.reverse()

    for operation in operations:
        operation_type = operation.operation_type.value
        if operation.status != 'Done':
            continue
        if operation_type != 'Buy' and operation_type != 'Sell':
            continue

        operationdate = operation.date - datetime.timedelta(hours=3)
        operationdate = operationdate.combine(operationdate.date(), operationdate.min.time())

        if operationdate != currentdate:
            if not consolidated:
                if oborot_usd != 0:
                    oborot_rub = round(oborot_rub, 2)
                    oborot_usd = round(oborot_usd, 2)
                    commission_rub = round(commission_rub, 2)
                    commission_usd = round(commission_usd, 2)
                    profit_rub = round(profit_rub, 2)
                    profit_usd = round(profit_usd, 2)
                    efficiency = round(profit_usd / oborot_intraday * 200, 2) if oborot_intraday != 0 else round(Decimal('0'), 2)
                    current_day = currentdate.strftime("%Y-%m-%d")
                    summary_table.add_row([current_day, oborot_usd, oborot_rub, commission_usd, commission_rub, profit_usd, profit_rub, efficiency, num_of_trades])
                oborot_rub = Decimal('0')
                oborot_usd = Decimal('0')
                oborot_intraday = Decimal('0')
                commission_rub = Decimal('0')
                commission_usd = Decimal('0')
                profit_rub = Decimal('0')
                profit_usd = Decimal('0')
                num_of_trades = 0
                table_trades = dict()

            rates = ExchangeRates(currentdate)
            currentdate = operationdate

        num_of_trades += 1
        payment = abs(Decimal(operation.payment))
        currency = operation.currency.value
        if currency == 'RUB':
            rate_for_rub = 1
            rate_for_usd = Decimal(1) / Decimal(rates['USD'].value)
        elif currency == 'USD':
            rate_for_rub = Decimal(rates['USD'].value)
            rate_for_usd = 1
        else:
            rate_for_rub = rates[currency].value
            rate_for_usd = Decimal(1) / Decimal(rates['USD'].value) * Decimal(rates[currency].value)
        oborot_rub += payment * rate_for_rub
        oborot_usd += payment * rate_for_usd

        commission = abs(Decimal(operation.commission.value)) if operation.commission else 0
        commission_rub += commission * rate_for_rub
        commission_usd += commission * rate_for_usd

        figi = operation.figi

        if figi not in dict_turnovers:
            dict_turnovers[figi] = payment * rate_for_usd
        else:
            dict_turnovers[figi] += payment * rate_for_usd

        quantity = operation.quantity_executed if operation_type == 'Buy' else -operation.quantity_executed
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
            profit_rub += profit_day * rate_for_rub
            profit_usd += profit_day * rate_for_usd
            oborot_intraday += (table_trades[figi]['sell'] + table_trades[figi]['buy']) * rate_for_usd
            oborot_intraday_summary += (table_trades[figi]['sell'] + table_trades[figi]['buy']) * rate_for_usd
            if figi not in dict_day_profits:
                dict_day_profits[figi] = profit_day * rate_for_usd
            else:
                dict_day_profits[figi] += profit_day * rate_for_usd
            del table_trades[figi]

    oborot_rub = round(oborot_rub, 2)
    oborot_usd = round(oborot_usd, 2)
    commission_rub = round(commission_rub, 2)
    commission_usd = round(commission_usd, 2)
    profit_rub = round(profit_rub, 2)
    profit_usd = round(profit_usd, 2)
    efficiency = round(profit_usd / oborot_intraday * 200, 2) if oborot_intraday != 0 else round(Decimal('0'), 2)

    current_day = currentdate.strftime("%Y-%m-%d")

    if consolidated:
        current_day = startdate.strftime("%Y-%m-%d") + " .. " + current_day

    summary_table.add_row([current_day, oborot_usd, oborot_rub, commission_usd, commission_rub, profit_usd, profit_rub, efficiency, num_of_trades])

    if len(summary_table.get_string().split("\n")) > 5:  # If more than one day in the table, then it's need to display the line with totals
        calculate_totals(summary_table, oborot_intraday_summary)
        print_with_footer(summary_table)
    else:
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
    date_without_sec = datetime.datetime.strptime(date_str, format_date).date()
    return datetime.datetime.combine(date_without_sec, datetime.time(2, 0))


def get_period(args, to_reversed):
    nop = len(args)
    first_date = None
    second_date = None
    date2 = None
    if nop > 1:
        first_date = args[1]
    if nop > 2:
        second_date = args[2]
    today = get_now() - datetime.timedelta(hours=3)
    if first_date is None or first_date.lower() == "today":
        date1 = today
        to_reversed = False
    elif first_date.lower() == "yesterday":
        date1 = today - datetime.timedelta(days=1)
    elif first_date.lower() == "thisweek":
        date2 = today
        weekday = date2.weekday()
        date1 = today - datetime.timedelta(days=weekday)
    elif first_date.lower() == "thismonth":
        date2 = today
        date1 = today.replace(day=1, hour=2, minute=0, second=0, microsecond=0)
    elif first_date.lower() == "thisyear":
        date2 = today
        date1 = today.replace(month=1, day=1, hour=2, minute=0, second=0, microsecond=0)
    elif first_date.lower() == "lastweek":
        weekday = today.weekday()
        date1 = (today - datetime.timedelta(days=weekday+7)).replace(hour=2, minute=0, second=0, microsecond=0)
        date2 = today - datetime.timedelta(days=weekday+1)
    elif first_date.lower() == "lastmonth":
        begin_month = today.replace(day=1, hour=2, minute=0, second=0, microsecond=0)
        date2 = begin_month - datetime.timedelta(days=1)
        date1 = date2.replace(day=1, hour=2, minute=0, second=0, microsecond=0)
    elif first_date.lower() == "lastyear":
        begin_year = today.replace(month=1, day=1, hour=2, minute=0, second=0, microsecond=0)
        date2 = begin_year - datetime.timedelta(days=1)
        date1 = date2.replace(month=1, day=1, hour=2, minute=0, second=0, microsecond=0)
    else:
        date1 = get_date_from_string(first_date)
    if date2 is None and second_date is not None:
        date2 = get_date_from_string(second_date)
    if date2 is not None and date2 < date1:
        date1, date2 = date2, date1

    return date1, date2


if __name__ == "__main__":
    to_reversed = True
    args = sys.argv
    date1, date2 = get_period(args, to_reversed)

    consolidated = False
    if (len(args) > 2 and args[2].lower() == "cons") or (len(args) > 3 and args[3].lower() == "cons"):
        consolidated = True

    operations = tinkoff.get_operations(date1, date2)
    day_results(operations, date1, to_reversed, consolidated)
