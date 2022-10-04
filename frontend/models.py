from django.db import models


# Create your models here.
class Ticker(models.Model):
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=20)
    company_name = models.CharField(max_length=200)
