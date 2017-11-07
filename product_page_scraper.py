# -*- coding: utf-8 -*-

import requests
import html
from bs4 import BeautifulSoup
import random
from product import Produkt
import time
import json

class PageScraper:

    def __init__(self, file_with_products_url, log_in=False, file_is_json_dump=True):
        self.file_with_products_url = file_with_products_url
        self.product_urls = {}
        self.scraped_products = []
        self.session = None
        self.soup = None
        self.log_in = log_in
        self.file_is_json_dump = file_is_json_dump

    def get_urls_from_file(self):
        with open(self.file_with_products_url, 'r') as file:
            if self.file_is_json_dump:
                data = json.loads(file.read())
                self.product_urls = data
            else:
                urls = [i for i in file.read().split('\n')]
                urls = [i.split(',')[1].strip() for i in urls if 'Error' not in i]
                self.product_urls = urls
                #  random.shuffle(self.product_urls)

    def login_to_highlite(self, login, password):
        with requests.Session() as session:
            self.session = session
            headers = requests.utils.default_headers()
            headers.update({'User-Agent': 'I\'m friendly. I\'m scraping some info about you\'r products. '
                                          'Contact: BLASK (Poland), Michael Dabrowski (I\'m your customer).'})
            self.session.headers = headers
            if self.log_in:
                login_payload = {'Login': login, 'Password': password}
                login_url = "http://www.highlite.nl/user/login"
                self.session.post(login_url, data=login_payload)

    def create_soup(self, url):
        if self.log_in:
            response = self.session.get(url)
        else:
            headers = requests.utils.default_headers()
            headers.update({'User-Agent': 'I\'m friendly. I\'m scraping some info about you\'r products. '
                                          'Contact: BLASK (Poland), Michael Dabrowski (I\'m your customer).'})
            response = requests.get(url, headers=headers)
        self.soup = BeautifulSoup(response.content, "lxml")

    def get_name(self):
        content = self.soup.find_all('div', class_='heading')
        name = content[0].text
        name = name.strip()
        name = name.split('\n')
        name = name[0]
        return name

    def get_sub_name(self):
        content = self.soup.find_all('div', class_='heading')
        try:
            name = content[0].text
            name = name.strip()
            name = name.split('\n')
            name = name[1]
            return name
        except IndexError:
            return ''

    def get_bullet_points(self):
        content = self.soup.find_all('div', class_='information')
        try:
            points = content[0].contents[3]
            points = ''.join([str(i) for i in points])
            return points
        except IndexError:
            return ''

    def get_description(self):
        content = self.soup.find_all('div', id='tab-10')
        try:
            content = content[0].contents[1]
            description = ''
            for element in content:
                description += str(element)
            description = description.strip()
            return description
        except IndexError:
            return ''

    def get_technical_data(self):
        content = self.soup.find_all('div', id='tab-10')
        try:
            content = content[0]
            technical_data = ''.join(
                [str(i) for i in content.contents[3].contents[1]]
            ).replace('<h3>Specifications</h3>','').strip()
            return technical_data
        except IndexError:
            return ''

    def get_video_link(self):
        content = self.soup.find_all('div', class_='video')
        try:
            content = content[0].contents[1].get('src')
            return content
        except IndexError:
            return ''

    def get_product_code(self):
        content = self.soup.find_all('div', class_='code')
        code = content[0].contents[3].text
        return code

    def get_availability(self):
        """Needs AJAX request"""
        pass

    def get_categories(self):
        content = self.soup.find_all('ul', class_='breadcrumbs')
        content = content[0]
        manufacturer = content.contents[1].text
        main_category = content.contents[3].text
        subcategory1 = content.contents[5].text
        subcategory2 = content.contents[7].text
        name = content.contents[9].text
        subcategory3 = ''
        return {'manufacturer': manufacturer,
                'main_category': main_category,
                'subcategory1': subcategory1,
                'subcategory2': subcategory2,
                'subcategory3': subcategory3,
                'name': name
                }

    def get_images(self):
        images_list = []
        content = self.soup.find_all('div', class_='images')
        try:
            content = content[0:25]  #  our database can have max. 25 images
            for image in content:
                 image = image.contents[1].contents[1].get('data-larg-image')
                 image = "http://www.highlite.nl" + image
                 images_list.append(image)
            images_dict = {'foto' + str(index): value for (index, value) in enumerate(images_list, start=1)}
            return images_dict
        except IndexError:
            return {}

    def create_product_object(self):
        produkt = Produkt()
        produkt.nazwa = self.get_name()
        produkt.dopisek = self.get_sub_name()
        produkt.kod_produktu = self.get_product_code()
        produkt.opis = self.get_description()
        produkt.cechy = self.get_bullet_points()
        produkt.dane_tech = self.get_technical_data()
        produkt.video = self.get_video_link()

        categories = self.get_categories()
        produkt.kategoria = categories['main_category']
        produkt.podkategoria1 = categories['subcategory1']
        produkt.podkategoria2 = categories['subcategory2']
        produkt.podkategoria3 = categories['subcategory3']
        produkt.producent = categories['manufacturer']

        images = self.get_images()
        produkt.update(images)  #  updates produkt.foto1, produkt.foto2 etc. with a dictionary {'foto1': link, 'foto2': link etc.}
        return produkt

    def save_json_to_file(self):
        with open('json_data.txt', 'w') as file:
            data_dump = json.dumps(self.scraped_products)
            file.write(data_dump)

    def main(self):
        count = 1
        self.get_urls_from_file()
        self.login_to_highlite('login', 'password')
        for code, url in self.product_urls.items():
            self.create_soup(url)
            product = self.create_product_object()
            self.scraped_products.append(product.__dict__)
            print('Scraping {}. Product {} of {}. Foto1: {}'.format(product.nazwa, str(count), str(len(self.product_urls)), product.foto1))
            self.save_json_to_file()
            count += 1
            time.sleep(random.uniform(3, 5))

if __name__ == "__main__":
    scraper = PageScraper(file_with_products_url='missing_products_links_1.txt',
                          log_in=False
                          )
    scraper.main()

