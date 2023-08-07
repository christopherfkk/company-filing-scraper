# Company Financial Statement Filing Scraper

- I scraped and assembled 10 years of SEC financial statement filings for a given company
- The data can then be used to feed into stock price valuation models, such as the dividend return model, or discounted cash flow model
- I deployed a minimal Python Django web application on Heroku at https://pacific-island-17482.herokuapp.com/frontend that takes a company ticker and returns a table of the company's financial data with each column being a year. UPDATE: unfortunately I ran out of Heroku credits to keep it running.
- The scraper is at [back/scraper.py](backend/scraper.py)

## Run the minimal web application locally (MacOS)

Create a virtual environment and install dependencies. Then start a Django development server.
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
