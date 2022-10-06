from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext
import pandas as pd

from backend.scraper import SECScraper


# Create your views here.
def index(request):
    return render(request, "frontend/index.html")


def result(request):
    if request.method == 'POST':

        # Take user input
        ticker = str(request.POST['ticker'])

        # Rune backend scraper
        scraper = SECScraper(ticker=ticker)
        df = scraper.execute()

        # # Setup response type
        # response = HttpResponse(
        #     content_type='text/csv',
        #     headers={'Content-Disposition': f'attachment; filename={ticker}_filings.csv'},
        # )
        #
        # # Convert DataFrame to CSV
        # df.to_csv(
        #     path_or_buf=response,
        #     sep=';',
        #     float_format='%.2f',
        #     index=False,
        #     decimal=","
        # )
        return render(request, 'frontend/result.html', {'df': df})
