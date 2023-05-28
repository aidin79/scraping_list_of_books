from datetime import time
import numpy as np
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from time import sleep
from urllib.parse import urlparse
from URL_LIST import URL_LIST
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import re

start = datetime.now()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))


def book_dict_gen(book_div):
    book_dict = {}
        
    name = book_div.find('h5').text
    uncleaned_details = book_div.find('p')
    price = book_div.find('h6')
    publisher = book_div.find('div', class_='description').text.replace('\n', '').replace('\t', '')
    book_dict['name'] = name
    book_dict['publisher'] = publisher
    book_dict['price'] = int(price.text[:-5].replace(',', ''))
        
    fetch_book_details(book_dict, uncleaned_details)
    return book_dict

def fetch_book_details(book_dict, uncleaned_details):
    enums = {
            'ناشر': 'publiser',
            'نويسنده': 'auther',
            'به\u200cاهتمام': 'diligently',
            'زيرنظر': 'onder review of',
            'سال انتشار': 'publish year',
            'شابک': 'ISBN',
            'نوبت چاپ': 'publication times',
            'شمارگان': 'numbers',
            'تصويرگر': 'painter',
            'شاعر': 'poet',
            'گردآورنده': 'collector',
            'مترجم': 'translator',
            'بازنويسي': 'rewriter',
            'تدوين': 'composition',
            'ويراستار': 'editor',
            'گرافيست': 'graphist',
            'محقق': 'researcher'
        }
    cleaned_details_list = list(filter(None, uncleaned_details.text.strip().replace('\t', '').split('\n')))
    for detail in cleaned_details_list:
        colon_index = detail.find(':')
        if detail[:colon_index] not in enums:
            continue
        key = enums[detail[:colon_index]]
        value = detail[colon_index + 1:]
        book_dict[key] = value

def fetch_num_of_pages(driver, book_div):
    driver.get('https://book.icfi.ir' + book_div.parent['href'])
    content = driver.page_source
    soup = BeautifulSoup(content, features='html.parser')
    details_str = soup.find_all('p')[1].text.replace('\t', '')
    index_of_num_of_pages = details_str.find('تعداد صفحات:')
    if index_of_num_of_pages == -1:
        return -1
    num_of_pages = details_str[index_of_num_of_pages + 13 : index_of_num_of_pages + 17]
    driver.back()
    return int(num_of_pages)

def save_df_as_pdf():
    df = pd.DataFrame(np.random.random((10,3)), columns = ("col 1", "col 2", "col 3"))

    #https://stackoverflow.com/questions/32137396/how-do-i-plot-only-a-table-in-matplotlib
    fig, ax =plt.subplots(figsize=(12,4))
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=df.values,colLabels=df.columns,loc='center')

    #https://stackoverflow.com/questions/4042192/reduce-left-and-right-margins-in-matplotlib-plot
    pp = PdfPages("foo.pdf")
    pp.savefig(fig, bbox_inches='tight')
    pp.close()


books = []

try:
    for i, url in enumerate(URL_LIST):
        page_number = 1
        driver.get(url)
        while True:
            
            content = driver.page_source
            soup = BeautifulSoup(content, features='html.parser')
            
            for book_div in soup.find_all('div', attrs={'class':'bookitem'}):
                book_dict = book_dict_gen(book_div)
                book_dict['num of pages'] = fetch_num_of_pages(driver, book_div)
                books.append(book_dict)
                
            angle_left_element = soup.find('i', class_='fa-angle-left')
            is_last_page = angle_left_element.parent.parent.has_attr("class")
            
            if is_last_page:
                break
            
            page_number += 1
            parsed_url = urlparse(url)
            driver.get('https://book.icfi.ir/book?page=' + str(page_number) + '&' + parsed_url.query)
            sleep(1)
        print('page {} has read'.format(i))
finally:
    end = datetime.now()
    diff = end - start
    print(diff)

    df = pd.DataFrame(books)
    # df.to_csv('selected.csv')
    df['price'] = df['price'] * 0.09
    df['page / price'] = df['num of pages'] / df['price'] * 1000
    df.sort_values('page / price', inplace=True, ascending=False)
    df.to_csv('selected.csv', index=False)