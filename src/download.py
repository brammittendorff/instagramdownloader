import time 
import os
import sys
import argparse
import urlparse
import json
import sqlite3
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

parser = argparse.ArgumentParser(description='Json downloader for instagram')
parser.add_argument('-l', '--url-list', metavar='file', type=argparse.FileType('r'), help='you can load urls to scrape', nargs='?')
parser.add_argument('-k', '--keywords', help='keyword seperated by comma e.g. cars,boats', nargs='?')
parser.add_argument('-s', '--save-dir', help='the dir to write save the images', nargs='?', required=True)

args = parser.parse_args()

if (args.url_list or args.keywords) and args.save_dir:

    timeout = 1

    load_dotenv()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS urls
            (url_id integer primary key AUTOINCREMENT,
            url varchar(255) NOT NULL)''')
    conn.commit()

    capabilities = webdriver.common.desired_capabilities.DesiredCapabilities.CHROME.copy()
    capabilities['javascriptEnabled'] = True

    options = webdriver.ChromeOptions()
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/75.0.3770.90 Chrome/75.0.3770.90 Safari/537.36')

    driver = webdriver.Remote(
        command_executor = 'http://localhost:4444/wd/hub',
        desired_capabilities = capabilities,
        options = options
    )

    # Login
    driver.get('https://www.instagram.com')
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.TAG_NAME, 'form'))
        )
        form_username = driver.find_element_by_name("username")
        form_password = driver.find_element_by_name('password')
        ActionChains(driver)\
            .move_to_element(form_username).click()\
            .send_keys(os.environ["INSTAGRAM_USERNAME"])\
            .move_to_element(form_password).click()\
            .send_keys(os.environ["INSTAGRAM_PASSWORD"])\
            .perform()
        form_submit = driver.find_element_by_xpath("//button[@type='submit']")
        form_submit.click()
    except TimeoutException:
        pass

    # Scrape by keywords
    if args.keywords:
        keywords = args.keywords.split(',')
        for word in keywords:
            driver.get('https://www.instagram.com/explore/tags/' + word + '/')
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.TAG_NAME, 'article'))
                )
                articles = driver.find_element_by_tag_name('article')
                items = articles.find_elements_by_xpath('//a[contains(@href,"/p/")]')
                # Loop trough found items
                for item in items:
                    url = item.get_attribute('href')
                    c.execute("SELECT * FROM urls WHERE url=?", (url,))
                    databse_url = c.fetchone()
                    if databse_url is None:
                        # Download image
                        my_folder = args.save_dir
                        if not os.path.exists(my_folder):
                            os.makedirs(my_folder)
                        image_url = item.find_element_by_tag_name('img').get_attribute('src')
                        parsed_url = urlparse.urlparse(image_url)
                        image_name = os.path.basename(parsed_url.path)
                        img_data = requests.get(image_url).content
                        with open(my_folder + image_name, 'wb') as handler:
                            handler.write(img_data)
                        # Insert image into sqlite3, so we do not download it again
                        c.execute("INSERT INTO urls ('url') VALUES ('" + item.get_attribute('href') + "')")
                        conn.commit()
            except TimeoutException:
                pass

    conn.close()
    driver.quit()