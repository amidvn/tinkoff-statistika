import datetime
import locale

from prettytable import PrettyTable


class OutputTable(object):
    def __init__(self) -> None:
        self.columns = ["date", "turnover_usd", "turnover_rub", "commission_usd", "commission_rub", "margin",
                        "profit_usd", "profit_rub", "efficiency", "num_of_operations", "num_of_trades"]
        self.data = dict()

    def set_value(self, day, column, value):
        if day not in self.data:
            self.data[day] = RowOT(day)
        D = self.data[day]
        D[column] += value

    def __str__(self):
        return self.get_string()

    def get_string(self, **kwargs):
        if len(self.data) == 0:
            return ""

        locale.setlocale(locale.LC_ALL, '')

        column_matching_rus = {
            "date": "День",
            "turnover_usd": "Оборот, $",
            "turnover_rub": "Оборот, ₽",
            "commission_usd": "Комиссия, $",
            "commission_rub": "Комиссия, ₽",
            "margin": "Марж., ₽",
            "profit_usd": "Финрез, $",
            "profit_rub": "Финрез, ₽",
            "efficiency": "Эфф-сть, %",
            "num_of_operations": "Операций",
            "num_of_trades": "Закр. сделок",
        }
        column_matching_eng = {
            "date": "Day",
            "turnover_usd": "Turnover, $",
            "turnover_rub": "Turnover, ₽",
            "commission_usd": "Comm., $",
            "commission_rub": "Comm., ₽",
            "margin": "Marg., ₽",
            "profit_usd": "Profit/loss, $",
            "profit_rub": "Profit/loss, ₽",
            "efficiency": "Efficiency, %",
            "num_of_operations": "Am. of oper.",
            "num_of_trades": "Am. of trades",
        }
        field_names = []
        for column in self.columns:
            field_names.append(column_matching_rus[column])
        summary_table = PrettyTable()
        summary_table.field_names = field_names
        summary_table.align = "r"
        summary_table.align[field_names[0]] = "c"

        summaries = RowOT("ИТОГО")
        if "efficiency" not in summaries:
            summaries["efficiency"] = 0.0
        column_efficiency = self.columns.index("efficiency")
        D = self.data
        for current_day in D:
            cur_val = D[current_day]
            row = []
            for column in self.columns:
                value = cur_val[column]
                if isinstance(value, float) or isinstance(value, int):
                    summaries[column] += value
                if isinstance(value, float):
                    value = locale.format('%.2f', value, grouping=True)
                elif isinstance(value, int):
                    value = locale.format('%.d', value, grouping=True)
                row.append(value)
            turnover_intraday = cur_val["turnover_intraday"]
            summaries["turnover_intraday"] += turnover_intraday
            if isinstance(row[0], datetime.datetime):
                row[0] = row[0].strftime("%Y-%m-%d")
            row[column_efficiency] = round(cur_val["profit_usd"] / turnover_intraday * 200, 2) if turnover_intraday != 0 else round(0.0, 2)
            summary_table.add_row(row)

        if len(D) == 0:
            return "Нет данных к выводу"
        elif len(D) == 1:
            return summary_table.get_string()
        else:
            # calculate totals
            summary_row = []
            for column in self.columns:
                value = summaries[column]
                if isinstance(value, float):
                    value = locale.format('%.2f', value, grouping=True)
                elif isinstance(value, int):
                    value = locale.format('%.d', value, grouping=True)
                summary_row.append(value)
            turnover_intraday = summaries["turnover_intraday"]
            summary_row[column_efficiency] = round(summaries["profit_usd"] / turnover_intraday * 200, 2) if turnover_intraday != 0 else round(0.0, 2)
            summary_table.add_row(summary_row)

            # Print a prettytable with an extra delimiter before the last `num_footers` rows
            lines = summary_table.get_string().split("\n")
            hrule = lines[0]
            num_footers = 1
            lines.insert(-(num_footers + 1), hrule)
            return "\n".join(lines)


class RowOT(dict):
    def __init__(self, date) -> None:
        self["date"] = date
        self["turnover_usd"] = 0.0
        self["turnover_rub"] = 0.0
        self["turnover_intraday"] = 0.0
        self["commission_usd"] = 0.0
        self["commission_rub"] = 0.0
        self["margin"] = 0.0
        self["margin_usd"] = 0.0
        self["profit_usd"] = 0.0
        self["profit_rub"] = 0.0
        self["efficiency"] = 0.0
        self["num_of_operations"] = 0
        self["num_of_trades"] = 0


if __name__ == "__main__":
    pass
