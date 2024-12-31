import requests
from bs4 import BeautifulSoup
from time import sleep
import re
import pandas as pd
import time
import os  # Import the os module
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service as Chromeservice
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.chrome import ChromeDriverManager
import csv
import getpass
from datetime import datetime, timedelta

driver = webdriver.Chrome(service = Chromeservice(ChromeDriverManager().install()))



def extract_data(card):
    username = card.find_element(By.XPATH,'.//span').text
    tweet_text_element = card.find_element(By.XPATH, '//div[@data-testid="tweetText"]').text
    tweet = (username, tweet_text_element)
    return tweet

def start_scraping(hashtag):

    print("started")
    
    data = []
    tweet_ids = set()
    last_position = driver.execute_script("return window.pageYOffset;")
    
    search = driver.find_element(By.XPATH, "//input[@placeholder='Search']")
    search.click()  # Click to focus on the search box
    search.send_keys(Keys.CONTROL + "a")  # Select all text
    search.send_keys(Keys.DELETE)  # Delete selected text
    search.send_keys(hashtag)  # Enter the hashtag
    search.send_keys(Keys.ENTER)  # Press Enter to initiate search
    time.sleep(8)
    scrolling = True
    
    output_filename = "s.csv"

    while scrolling:
        pages = driver.find_elements(By.CSS_SELECTOR,'[data-testid="tweet"]')
        for card in pages:
            tweet = extract_data(card)
            if tweet:
                tweet_id = " ".join(tweet)
                if tweet_id not in tweet_ids:
                    data.append(tweet)
            
                    
        scroll_attempts = 0
        while True:
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(1)
            current_position = driver.execute_script("return window.pageYOffset;")
            if current_position == last_position:
                scroll_attempts += 1
                
                if scroll_attempts >= 3:
                    scrolling = False
                    break
                
                else:
                    time.sleep(3)
            else:
                last_position = current_position
                break

            try:
                retry_button = driver.find_element(By.XPATH, "//div[@class='css-175oi2r r-sdzlij r-1phboty r-rs99b7 r-lrvibr r-2yi16 r-1qi8awa r-ymttw5 r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l']")  # Adjust the XPath according to your actual HTML structure
                retry_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Retry')]")))
                retry_button.click()
                print("clicked retry")
                # Wait for the page to load after clicking "Retry"
                time.sleep(5)  # Adjust the wait time as needed
            except:
                pass
                
            if len(data) >= 10:
                scrolling = False
                break

    filename, file_extension = os.path.splitext(output_filename)
    output_filename = f"{filename}_{query[-2:]}_{query[-5:-3]}_{query[-10:-6]}{file_extension}"
    
    with open(output_filename, 'w', newline='', encoding='utf-8') as file:
        headers = ["username","tweet_text_element"]
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(list(set(data)))

def generate_search_queries(keyword, days):
    queries = []
    end_date = datetime.date(2024, 3, 14)
    start_date = end_date - timedelta(days=days)  # Adjusted to subtract one day less
    delta = timedelta(days=2)
    
    while start_date <= end_date:
        next_date = start_date + delta
        query = f'{keyword} until:{next_date.strftime("%Y-%m-%d")} since:{start_date.strftime("%Y-%m-%d")}'
        print(query)
        queries.append(query)
        start_date += delta
    return queries


keyword = "zomato lang:en "
search_queries = generate_search_queries(keyword, 100)

driver.get('https://twitter.com/i/flow/login')
driver.maximize_window()
time.sleep(5)

driver.find_element(By.XPATH,"//input[@name='text']").send_keys('beproject2024') #add yourusername beproject2024 beproject2024_1 I_AM_AKHILE5H
time.sleep(1)
driver.find_element(By.XPATH,"//span[contains(text(),'Next')]").click()
time.sleep(3)
driver.find_element(By.XPATH,"//input[@name='password']").send_keys("Beproject@24")#enter password Beproject@24 
time.sleep(1)
driver.find_element(By.XPATH,"//span[contains(text(),'Log in')]").click()
time.sleep(10)

for query in search_queries:
    start_scraping(query)
