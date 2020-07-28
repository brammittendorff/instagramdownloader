import os
import sys
import time 
import glob
import math
import tempfile
import shutil
import atexit
import argparse
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
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

from classify import classify_image

def download_image(url, image_url):
    c.execute("SELECT * FROM urls WHERE url=?", (url,))
    databse_url = c.fetchone()
    if databse_url is None:
        # Download image
        print("Downloading url: {}".format(url))
        my_folder = args.save_dir
        if not os.path.exists(my_folder):
            os.makedirs(my_folder)
        parsed_url = urlparse(image_url)
        image_name = os.path.basename(parsed_url.path)
        img_data = requests.get(image_url).content
        with open(my_folder + image_name, 'wb') as handler:
            handler.write(img_data)
        # Insert image into sqlite3, so we do not download it again
        c.execute("INSERT INTO urls ('url', 'image_name') VALUES ('{}', '{}')".format(url, image_name))
        # Classify image
        classified_image = classify_image(my_folder + image_name)
        if classified_image:
            c.execute("INSERT INTO classified ('url_id', 'gender', 'gender_conf', 'age', 'age_conf') VALUES ({}, {}, '{}', {}, '{}')".format(c.lastrowid, classified_image['gender'], classified_image['genderprediction'], classified_image['age'], classified_image['ageprediction']))
        conn.commit()
        return True
    else:
        return False

# Directory check for argparse
class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))

ldir = tempfile.mkdtemp()
atexit.register(lambda dir=ldir: shutil.rmtree(ldir))

array_error = [
    "Sorry, this page isn't available."
]

parser = argparse.ArgumentParser(description='Json downloader for instagram')
parser.add_argument('-s', '--save-dir', help='the dir to write save the images', nargs='?', required=True)
parser.add_argument('-d', '--url-list-dir', action=readable_dir, default=ldir, nargs='?')
parser.add_argument('-k', '--keywords', help='keyword seperated by comma e.g. cars,boats', nargs='?')

args = parser.parse_args()

if (args.url_list_dir or args.keywords) and args.save_dir:

    timeout = 1
    error_times = 0

    load_dotenv()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Create urls table
    c.execute('''CREATE TABLE IF NOT EXISTS urls
            (url_id integer primary key AUTOINCREMENT,
            image_name varchar(255) NOT NULL,
            url varchar(255) NOT NULL)''')
    # Create classified table
    c.execute('''CREATE TABLE IF NOT EXISTS classified
            (classiefied_id integer primary key AUTOINCREMENT,
            url_id integer NOT NULL,
            gender integer NOT NULL,
            gender_conf decimal(10, 5) NOT NULL,
            age integer NOT NULL,
            age_conf decimal(10, 5) NOT NULL)''')
    conn.commit()

    capabilities = webdriver.common.desired_capabilities.DesiredCapabilities.CHROME.copy()
    capabilities['javascriptEnabled'] = True

    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/83.0.4103.61 Chrome/83.0.4103.61 Safari/537.36')

    driver = webdriver.Remote(
        command_executor = 'http://localhost:4444/wd/hub',
        desired_capabilities = capabilities,
        options = options
    )

    # Login
    driver.get('https://www.instagram.com')
    driver.maximize_window()
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
    
    time.sleep(2)

    # Scrape by hashtags
    if args.keywords:
        keywords = args.keywords.split(',')
        for word in keywords:
            driver.get("https://www.instagram.com/explore/tags/{}/".format(word))
            body = driver.find_element_by_css_selector('body')
            body.click()
            body.send_keys(Keys.PAGE_DOWN)
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.TAG_NAME, 'article'))
                )
                articles = driver.find_element_by_tag_name('article')
                items = articles.find_elements_by_xpath('//a[contains(@href,"/p/")]')
                # Loop trough found items
                for item in items:
                    print(item.find_element_by_tag_name('img').get_attribute('src'))
                    url = item.get_attribute('href')
                    image_url = item.find_element_by_tag_name('img').get_attribute('src')
                    if download_image(url, image_url):
                        print("Downloading url: {}".format(url))
                    else:
                        print("Already downloaded url: {}".format(url))
            except TimeoutException:
                pass

    # Scrape by <folder>/*.txt
    if args.url_list_dir:
        retval = os.getcwd()
        os.chdir(args.url_list_dir)
        for filename in glob.glob("*.txt"):
            with open(filename) as fp:
                line = fp.readline()
                while line:
                    # Needs this sleep because instagram doesn't like fast crawlers
                    # they will log you out automaticly
                    time.sleep(1)
                    driver.get(line.strip())
                    body = driver.find_element_by_css_selector('body')
                    body.click()
                    body.send_keys(Keys.PAGE_DOWN)
                    # If you got an error-container "Please wait a few minutes before you try again."
                    try:
                        element = WebDriverWait(driver, timeout).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, 'error-container'))
                        )
                        error_h2 = driver.find_element(By.CSS_SELECTOR, '.error-container h2')
                        if error_h2.text not in array_error:
                            error_times += 1
                            error_minutes = math.ceil((60 * error_times)/60)
                            print("Sleeping for a while because we need to wait a few minutes: {}".format(error_minutes))
                            time.sleep(60*error_times)
                    except TimeoutException:
                        pass
                    try:
                        element = WebDriverWait(driver, timeout).until(
                            EC.element_to_be_clickable((By.TAG_NAME, 'article'))
                        )
                        source = driver.page_source
                        # Get json data
                        if source:
                            strip1 = source.split(r'window._sharedData = ')
                            if len(strip1) > 1:
                                strip2 = strip1[1].split(r";</script>")
                                if strip2[0]:
                                    page_json = strip2[0]
                                    for json_object in json.loads(page_json)["entry_data"]["ProfilePage"]:
                                        user_media = json_object['graphql']['user']['edge_owner_to_timeline_media']
                                        if user_media.get("edges"):
                                            for node in user_media["edges"]:
                                                # Do not request urls to fast
                                                time.sleep(0.5)
                                                url = "https://instagram.com/p/{}/".format(node['node']["shortcode"])
                                                image_url = node['node']["display_url"]
                                                if download_image(url, image_url):
                                                    print("Downloading url: {}".format(url))
                                                else:
                                                    print("Already downloaded url: {}".format(url))
                    except TimeoutException:
                        pass
                    line = fp.readline()

    conn.close()
    driver.quit()