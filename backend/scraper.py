"""
This python file defines a class that scrapes the SEC EDGAR database of the United States
of America to gather relevant filing items of a specified company's annual financial
statements from the last 10 years. It then feeds the filing items in to a Google Spreadsheet
that automates the calculation of the specified company's fair market price.

This stock valuation bot foundations its algorithm on the fundamental investing outlook,
and prioritizes companies with a demonstrated history of high dividend yield.

1. Take "ticker" input from user
2. Search Central Index Key (CIK) from lookup
3. Crawl CIK/10-K search page
4. Get all 10-K filing base URL of the last ten years
    a. Access filing summary
    b. Map statement names and table url
    b. Scrape tables
    c. Store in DataFrame
    d. Update in GSheet
"""

import json
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import logging
import os
import lxml
from stock_valuation_webapp.settings import BASE_DIR


class SECScraper:

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.cik = None
        self.company = None
        self.headers = {"User-Agent": 'random@gmail.com'}
        self.all_10ks_summary_urls = []
        self.all_10ks_urls = []

    def execute(self) -> pd.DataFrame:

        self.get_ticker()
        self.find_cik()
        logging.info(f"\nSuccessfully found\n\tTicker: {self.ticker},\n\tCIK: {self.cik},\n\tCompany: {self.company}")

        self.get_10k_summary_urls()
        logging.info(f"Successfully found workable urls, e.g.\t{self.all_10ks_summary_urls[0]}")

        self.extract_10k_urls()
        logging.info(f"Successfully found 10K base urls, e.g.\t{self.all_10ks_urls[0]}")

        master_df = None
        years = 2
        for i in range(years):
            url = self.all_10ks_urls[i]
            mapping = self.find_statement_to_table_mapping_for_single_10k(url)
            logging.info(f"\t For Y{10-i}: Successfully found statement table urls")

            statements_data = self.scrape_data_for_single_10k(url, mapping)
            logging.info(f"\t For Y{10-i}: Successfully scraped statement data")

            if i == 0:
                df = self.make_df_for_single_10k(statements_data)
                master_df = df

            else:
                df = self.make_df_for_single_10k(statements_data)
                master_df = pd.concat([master_df, df], axis=1)

            logging.info(f"\t For Y{10 - i}: Successfully loaded into df")

        return master_df

    def get_ticker(self):
        self.ticker = self.ticker.strip().upper()

    def find_cik(self, return_cik: bool = False):

        # Open json lookup file
        with open(BASE_DIR / 'backend/static/cik.json', 'r') as file:
            lookup_json = json.load(file)

        # Convert to dataframe
        df = pd.json_normalize(pd.json_normalize(lookup_json, max_level=0).values[0])
        df["cik_str"] = df["cik_str"].astype(str).str.zfill(10)
        df.set_index("ticker", inplace=True)

        # Do lookup
        self.cik = df['cik_str'].loc[self.ticker.strip().upper()]
        self.company = df['title'].loc[self.ticker.strip().upper()]

        if return_cik:
            return self.cik

    def get_10k_summary_urls(self, return_urls: bool = False) -> list[str]:

        # Get search result page
        form = "10-K"
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.cik}&type={form}"
        response_text = requests.get(url, headers=self.headers).text

        # Scrape each 10-K summary page url
        soup = BeautifulSoup(response_text, features='lxml')
        tags = soup.find('div', id="seriesDiv").find_all('td', string="10-K")
        base = "http://sec.gov"
        for tag in tags:
            row = tag.parent
            link = row.find(id='documentsbutton').get('href')
            self.all_10ks_summary_urls.append(base+link)

        if return_urls:
            return self.all_10ks_summary_urls

    def extract_10k_urls(self, return_urls=False) -> list[str]:

        # Remove last bit of the summary url, add base url, and append
        for url in self.all_10ks_summary_urls:
            url = url.split('/')[:-1]
            url = '/'.join(url)
            self.all_10ks_urls.append(url)

        if return_urls:
            return self.all_10ks_urls

    def find_statement_to_table_mapping_for_single_10k(self, base_url: str) -> dict:

        # Access filing summary
        content = requests.get(base_url + "/FilingSummary.xml", headers=self.headers).content
        soup = BeautifulSoup(content, features='lxml')
        reports = soup.find('myreports')

        # Create mapping
        mapping = {}
        for report in reports.find_all('report')[:-1]:
            mapping[report.shortname.text.upper()] = report.htmlfilename.text

        return mapping

    def scrape_data_for_single_10k(self, base_url: str, mapping: dict) -> list[dict]:
        """
        This logic scrapes html files, which seems to be the case after 2010, suitable if only 10y of data.
        On 2010 for Apple, the table is in xml files, which requires another logic, shouldn't be too challenging tho
        """
        # statement_names_keyword = {
        #     "CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME":
        #         "comprehensive income",
        #     "CONSOLIDATED STATEMENTS OF CASH FLOWS":
        #         "cash flow",
        #     "CONSOLIDATED BALANCE SHEETS":
        #         "balance",
        #     "CONSOLIDATED STATEMENTS OF OPERATIONS":
        #         "operations"
        # }
        #
        # statements_url = []
        # failures = []
        # for name, keyword in statement_names_keyword.items():
        #     is_found = False
        #     try:
        #         statement_url = base_url + "/" + mapping[name]
        #         statements_url.append(statement_url)
        #         is_found = True
        #         logging.info(f"\tFound for {name} for {base_url}")
        #
        #     except KeyError:
        #         failures.append(name)
        #         logging.error(f"\tCannot find {name} for {base_url}")
        #
        #     if not is_found:
        #         logging.info(f"\tTrying keyword search for {name}")
        #
        #         # iterate "mapping", statement-name: html number dictionary
        #         for key in mapping.keys():
        #             if key[-1] == ")":
        #                 continue
        #             if keyword.upper() in key.upper():
        #                 is_found = True
        #                 statement_url = base_url + "/" + mapping[key]
        #                 statements_url.append(statement_url)
        #                 logging.info(f"\tKey word search for {name} found {statement_url}")
        #                 break
        #
        #         if not is_found:
        #             logging.error(f"\tKey word search for {name} failed")

        # Assume we want all the statements in a single data set.

        statements_url = []
        for i in range(2, 11):
            statement_url = base_url + "/" + f"R{i}.htm"
            statements_url.append(statement_url)

        statements_data = []
        for statement in statements_url:

            # Define a dictionary that will store the different parts of the statement.
            statement_data = {'headers': [], 'sections': [], 'data': []}

            # Request the statement file content
            content = requests.get(statement, headers=self.headers).content
            report_soup = BeautifulSoup(content, features='lxml')

            # Find all rows, figure out row type, parse the elements, and store in the statement file list.
            for index, row in enumerate(report_soup.table.find_all('tr')):

                # First let's get all the elements.
                cols = row.find_all('td')

                # If it's a regular row and not a section or a table header
                if len(row.find_all('th')) == 0 and len(row.find_all('strong')) == 0:
                    reg_row = [ele.text.strip() for ele in cols]
                    statement_data['data'].append(reg_row)

                # If it's a regular row and a section but not a table header
                elif len(row.find_all('th')) == 0 and len(row.find_all('strong')) != 0:
                    sec_row = cols[0].text.strip()
                    statement_data['sections'].append(sec_row)

                # If it's not any of those it must be a header
                elif len(row.find_all('th')) != 0:
                    hed_row = [ele.text.strip() for ele in row.find_all('th')]
                    statement_data['headers'].append(hed_row)

                else:
                    print('We encountered an error.')

            # Append it to the master list.
            statements_data.append(statement_data)
        return statements_data

    @staticmethod
    def make_df_for_single_10k(statements_data: list[dict]) -> pd.DataFrame:

        # Make df
        header = statements_data[0]['headers'][1]  # the dates
        data = []
        for i in range(len(statements_data)):
            data += statements_data[i]['data']
        df = pd.DataFrame(data)

        converted = []
        for i in range(len(header)):
            date = datetime.strptime(header[i], '%b. %d, %Y')
            converted.append(date)

        df = df.iloc[:, :2]  # Get the first four columns only
        category_column = f'Category {converted[0].year}'
        df.columns = [category_column] + header[:1]  # Assign column names

        # Drop empty categories
        df[category_column].replace('', np.nan, inplace=True)
        df.dropna(subset=[category_column], inplace=True)

        # Replace strings
        df = df.replace('[\$,)]', '', regex=True)  # replace '$', ',', '\', ')'
        df = df.replace('[(]', '-', regex=True)  # replace '(' with '-' for negative numbers

        # Strip strings
        df_obj = df.select_dtypes(['object'])
        df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())

        # Convert string to float type and fill null
        df = df.astype(float, errors='ignore')
        df.replace('', None, inplace=True)

        return df


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    scraper = SECScraper('MSFT')
    scraper.execute()


"""
Debug notes:

1) Naming of tables are different
        Apple "CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME" 
            Works
        Microsoft "COMPREHENSIVE INCOME STATEMENTS"
            keywords are in microsoft, just no operations
        Tesla "Consolidated Statements of Comprehensive Income (Loss)"
            Keywords are in tesla
        Meta
            Keywords are in meta, no operations
        Google
            Keywords are in, no operations
        Palantir
            No income sheet --> Consolidated Statements of Comprehensive Loss
        Twitter
            keywords in, comprehensive income is parenthesized with loss
        Uber
            keyword are in income is called --> CONSOLIDATED STATEMENTS OF COMPREHENSIVE LOSS
        Amazon
            seems to work
        Netflix
            seems to work
            
        
            
        
        
2) Might not have 10 years worth of 10-Ks
        Google/Alphabet has 10-K's since 2016
        
3) Even items under tables might be different
"""