from report_tools.reports import Report
from report_tools.chart_data import ChartData
from report_tools.renderers.googlecharts import GoogleChartsRenderer
from report_tools import charts
from helpline.models import *

class MyReport(Report):
    renderer = GoogleChartsRenderer

    pie_chart = charts.PieChart(
        title="A nice, simple pie chart",
        width=400,
        height=300
    )

    def get_data_for_pie_chart(self):
        data = ChartData()

        data.add_column("Pony Type")
        data.add_column("Population")

        data.add_row(["Blue", 20])
        data.add_row(["Pink", 20])
        data.add_row(["Magical", 1])

        return data

class DashBoardReport(Report):
    renderer = GoogleChartsRenderer
    answered_calls = report.objects.filter(calltype__exact='Answered').count()
    abandoned_calls = report.objects.filter(calltype__exact='Abandoned').count()
    voice_mails = recorder.objects.filter(hl_type__exact='Voicemail').count()

    pie_chart = charts.PieChart(
        title="Dashboard activity report",
        width=400,
        height=300
    )

    def get_data_for_pie_chart(self):
        data = ChartData()
        data.add_column("Calls")
        data.add_column("Number")

        data.add_row(["Answered",626])
        data.add_row(["Abandoned",323])
        data.add_row(["Voice Mail",9])

        return data
