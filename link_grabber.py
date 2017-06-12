# -*- coding: utf-8 -*-

import requests
import html
from bs4 import BeautifulSoup
import random
import time
from product import Produkt
from product_page_scraper import PageScraper

class ProductsLinkGrabber:
    """
    Grabs links to products using product codes. Works with highlite.nl
    Needs product codes (file)
    Saves a file 'missing_products_links.txt'
    """
    def __init__(self, file_with_product_codes):
        self.missing_items_codes = []
        self.session = None
        self.missing_items_links = []
        self.file_with_product_codes = file_with_product_codes

    def update_missing_items_codes_from_file(self):
        file = open(self.file_with_product_codes, 'r')
        file = [i for i in file.read().split('\n')]
        self.missing_items_codes = file
        #  random.shuffle(self.missing_items_codes)

    def json_search_for_product_link(self, product_code):
        time.sleep(random.uniform(1, 3))
        product_code_ajax = ''.join([i for i in product_code if i.isdigit()])
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0'}
        url = 'https://www.highlite.nl/ezjscore/call/'
        json_payload = {'search_text': product_code_ajax,
                'ezjscServer_function_arguments': "ezjsctemplate::search_autocomplete_ajax",
                'ezxform_token': ""
                        }
        response = requests.post(url, data=json_payload, headers=headers)
        response = str(response.content)
        parsed = html.unescape(response)
        soup = BeautifulSoup(parsed, "lxml")
        content = soup.find_all('a')
        for element in content:
            response_code = element.text
            if response_code == product_code:
                link = element.get('href')
                link = str(product_code) + ', ' + "http://www.highlite.nl" + link
                print('Getting link: ' + link)
                return link
        link = 'Error retrieving data for ' + str(product_code)
        return link

    def save_missing_products_links_to_file(self):
        with open('missing_products_links.txt', 'w') as file:
            for link in self.missing_items_links:
                file.write(link + '\n')

    def main(self):
        count = 1
        self.update_missing_items_codes_from_file()
        for code in self.missing_items_codes:
            print("Code " + str(count) + ' from ' + str(len(self.missing_items_codes)))
            link = self.json_search_for_product_link(code)
            self.missing_items_links.append(link)
            self.save_missing_products_links_to_file()
            count += 1

if __name__ == "__main__":
    u = ProductsLinkGrabber('missing_items.txt')
    u.main()