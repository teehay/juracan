#!/usr/bin/env python3
# JURACAN 0.1 by teehay

# A Python(3) script that uses Firefox and Selenium to search the Hurricane Electric Internet Services website for a keyword and output
# or store the results. Please do not abuse the service by spamming requests.

# Current feature priority:
# Connect script to databases and add corresponding flags

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
import argparse
import sys
import mysql.connector #to be added
import sqlite3

if __name__ == "__main__":

    ## Handle args
    parser = argparse.ArgumentParser(description='Gets ASN and ISP addresses related to the target keyword from the Hurricane Electric Internet Services website. Please do not abuse this service!')
    parser.add_argument('keyword', metavar='keyword', type=str, nargs='?', help='target keyword')
    parser.add_argument('--sqlite',  metavar=('dbpath', 'tablename'), nargs=2, help='store results in a SQLite database')

    if len(sys.argv) < 2:
        parser.print_usage()
        sys.exit(1)
    else:
        arg = parser.parse_args()

    ## Set up WebDriver
    options = Options()
    options.add_argument('-headless')

    driver = Firefox(executable_path='/usr/bin/geckodriver', options=options)
    wait = WebDriverWait(driver, timeout=10)
    driver.get('https://bgp.he.net')

    ## Perform search and wait for results to populate
    wait.until(expected.presence_of_element_located((By.NAME, 'search[search]'))).send_keys(arg.keyword + Keys.ENTER)
    wait.until(expected.element_to_be_clickable((By.NAME, 'commit'))).click()
    wait.until(expected.presence_of_element_located((By.TAG_NAME, 'table')))

    ## Set up BeautifulSoup and find individual results
    soup = BeautifulSoup(driver.page_source, features='lxml')
    results = soup.find_all('tr')

    if arg.sqlite:
        conn = sqlite3.connect(arg.sqlite[0])
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS " + arg.sqlite[1] + " (id INTEGER UNIQUE, result TEXT UNIQUE, description TEXT, country TEXT, PRIMARY KEY(id))")

    ## Cycle through results and print header, then results in formatted form
    for i in range(1, len(results)):
        if i == 1:
            print("Keyword: " + results[i].a.string)
            print(f"{'Results:':<44}{'Description:':<48}{'Country:':<16}")
        else:
            data = results[i].find_all('td')

            res = data[0].get_text()
            desc = data[1].get_text()
            country = data[1].div.img['title']

            print(f"{res:<44}{desc:<48}{country:<16}")

            if arg.sqlite:
                c.execute("INSERT INTO " + arg.sqlite[1] + " (result, description, country) VALUES (?, ?, ?)", (res, desc, country))

    if arg.sqlite:
        conn.commit()
        conn.close()
                  
    driver.quit()