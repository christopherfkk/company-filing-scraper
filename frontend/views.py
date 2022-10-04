from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext

from backend.scraper import SECScraper


# Create your views here.
def index(request):
    return render(request, "frontend/index.html")


def result(request):
    if request.method == 'POST':
        ticker = str(request.POST['ticker'])
        scraper = SECScraper(ticker=ticker)
        df = scraper.execute()
        return HttpResponse(str(df), RequestContext(request))
    else:
        return HttpResponse("Accessed by GET")
