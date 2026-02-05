#!/usr/bin/env python3
# JURACAN 1.5 by teehay

# A Python(3) script that uses Firefox (or Chrome) and Selenium to search the Hurricane Electric Internet Services website for a keyword and output
# or store the results. Please do not abuse the service by spamming requests.

#!!!!!! Currently not functional because of changes in the EIS result HTML. Can easily be fixed by bringing to date all instances of code that refer to the old HTML. !!!!!!

from selenium.webdriver import Firefox, Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options as firefox_options
from selenium.webdriver.chrome.options import Options as chrome_options
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
import argparse
import sys
import os
import mysql.connector
import sqlite3
import subprocess

if __name__ == "__main__":
    ## Handle args
    parser = argparse.ArgumentParser(description='Gets ASN and ISP addresses related to the target keyword from the Hurricane Electric Internet Services website. Please do not abuse this service!')

    ## Add trgt keyword argument
    parser.add_argument('keyword', metavar='keyword', type=str, nargs='?', help='target keyword')

    ## Adds the function of storing results in SQLite
    parser.add_argument('-s', '--sqlite',  metavar=('dbpath', 'tablename'), \
    nargs=2, help="store results in a SQLite database; creates a new database and table if they don't already exist")

    ## Adds the function of storing results in MySQL
    parser.add_argument('-m', '--mysql',  metavar=('host', 'dbname', 'tblname', 'user', 'password'),\
    nargs=5, help="store results in a MySQL database; creates a new database and table if they don't exist" )

    ## Add the ability to output table data as a CSV list
    parser.add_argument('-c', '--csv', action='store_true', \
    help="output table data as a CSV list")

    ## Allows output of the result column and format
    parser.add_argument('-r', '--result', action='store_true', \
    help="output the result column data only; if --csv is on, result column data is output as a CSV list")

    ## Specifies location path of driver executable used
    parser.add_argument('-e', '--exec', metavar='path', type=str, nargs='?', \
    help="specify the location path to the driver executable that will be used; checks system path by default")

    ## Specifies location path of browser binary
    parser.add_argument('-b', '--binary', metavar='path', type=str, nargs='?', \
    help="specify the location path to the browser binary that will be used; checks common locations by default")

    ## Specifies browser driver for search (chrome or gecko)
    parser.add_argument('-d', '--driver', metavar='initial', type=str, nargs='?', default='g', const='g',\
    help="specify the browser driver that will be used in the search; options: c[hrome], g[ecko]; default: g")

    ## "quiet" mode - no screen output
    parser.add_argument('-q', '--quiet', action='store_true', \
    help="run script with no screen output")

    if len(sys.argv) < 2:   ## If no args other than arg[0] exist, print usage menu and exit program:
        parser.print_usage()
        sys.exit(1)
    else: ## Parse args:
        arg = parser.parse_args()

    ## Get OS path in list form
    dummypath = dict(os.environ)['PATH'].split(os.pathsep) 

    ## Handle browser option
    if arg.driver == 'g': # Gecko (Firefox)
        options = firefox_options() # Call firefox config options
        options.add_argument('--headless') # Browser will fire in headless mode

        if arg.binary:  # If binary location is specified, add it to the config options
            options.binary_location = arg.binary

        if arg.exec: # If executable path is specified in arg.exec, add them to driver configurations for Firefox and instantiate the driver.
            driver = Firefox(executable_path=arg.exec, options=options)
        else:  # Otherwise, proceed with only the options for Firefox.
            driver = Firefox(options=options)

    elif arg.driver == 'c': # Chrome
        options = chrome_options() # As above, but for Chrome (line 73)
        options.add_argument('--headless') # As above, but for chrome (line 74)
        options.add_argument('--no-sandbox') # Allows use as root, use at own risk!

        if arg.binary:
            options.binary_location = arg.binary  #(line 77 for Chrome)

        if arg.exec: # (line 79)
            driver = Chrome(executable_path=arg.exec, options=options) # (line 80)
        else: # (line 81)
            driver = Chrome(options=options)  # (line 82)

    ## Navigate to site
    driver.get('https://bgp.he.net')

    ## Perform search and wait for results to populate
    wait = WebDriverWait(driver, timeout=20)

    try:
        wait.until(expected.presence_of_element_located((By.NAME, 'search[search]'))).send_keys(arg.keyword + Keys.ENTER)
        wait.until(expected.element_to_be_clickable((By.NAME, 'commit'))).click()
        wait.until(expected.presence_of_element_located((By.TAG_NAME, 'table')))
    except TimeoutException:
        print("Page has timed out while waiting for elements to load. Check your connection or try again later.")
        sys.exit(1)

    ## Set up BeautifulSoup and find individual results
    soup = BeautifulSoup(driver.page_source, 'lxml')
    results = soup.find_all('tr')

    ## Set up databases
    if arg.sqlite:
        sqliteconn = sqlite3.connect(arg.sqlite[0])
        c = sqliteconn.cursor()
        if arg.csv:
            c.execute("CREATE TABLE IF NOT EXISTS " + arg.sqlite[1] + " (csv TEXT PRIMARY KEY)")
        else:
            c.execute("CREATE TABLE IF NOT EXISTS " + arg.sqlite[1] + " (result TEXT PRIMARY KEY, description TEXT, country TEXT)")

    if arg.mysql:
        mysqlconn = mysql.connector.connect(host=arg.mysql[0], user=arg.mysql[3], password=arg.mysql[4])
        if mysqlconn.is_connected():
            cur = mysqlconn.cursor()
            cur.execute("CREATE DATABASE IF NOT EXISTS " + arg.mysql[1])
            cur.execute("USE " + arg.mysql[1])
            if arg.csv:
                cur.execute("CREATE TABLE IF NOT EXISTS " + arg.mysql[2] + " (csv LONGTEXT)")
            else:
                cur.execute("CREATE TABLE IF NOT EXISTS " + arg.mysql[2] + " (result VARCHAR(192) PRIMARY KEY, description VARCHAR(256), country VARCHAR(128))")

    ## Create list to hold values, then join as CSV string
    csvlist = []

    ## Print header, then results in formatted form
    for i in range(1, len(results)):
        if i == 1 and not arg.csv and not arg.result and not arg.quiet:
            print("Keyword: " + results[i].a.string)
            print(f"{'Results:':<44}{'Description:':<48}{'Country:':<16}")
        elif i > 1:
            data = results[i].find_all('td')

            res = data[0].get_text()
            desc = data[1].get_text()
            country = data[1].div.img['title']

            if arg.csv and arg.result:
                csvlist.append(res)
            elif arg.csv and not arg.result:
                if ',' in desc:
                    desc = "\"" + desc + "\""
                csvlist.extend([res, desc, country])
            elif not arg.csv and arg.result and not arg.quiet:
                print(f"{res:<44}")
            elif not arg.quiet:
                print(f"{res:<44}{desc:<48}{country:<16}")

            ## Handle database insertion
            if arg.sqlite:
                if arg.result and not arg.csv:
                    c.execute("INSERT INTO " + arg.sqlite[1] + " (result) VALUES (?)", (res,))
                elif not arg.result and not arg.csv:
                    c.execute("INSERT INTO " + arg.sqlite[1] + " (result, description, country) VALUES (?, ?, ?)", (res, desc, country))
                elif arg.csv and i == len(results) - 1:
                    c.execute("INSERT INTO " + arg.sqlite[1] + " (csv) VALUES (?)", (','.join(csvlist),))
            if arg.mysql:
                if arg.result and not arg.csv:
                    cur.execute("INSERT INTO " + arg.mysql[2] + " (result) VALUES (%s)",(res,))
                elif not arg.result and not arg.csv:
                    cur.execute("INSERT INTO " + arg.mysql[2] + " (result, description, country) VALUES (%s, %s, %s)", (res, desc, country))
                elif arg.csv and i == len(results) - 1:
                    cur.execute("INSERT INTO " + arg.mysql[2] + " (csv) VALUES (%s)", (','.join(csvlist),))

    ## Turn values list into CSV string
    if arg.csv:
        print(','.join(csvlist))

    ## Close db connections
    if arg.sqlite:
        sqliteconn.commit()
        sqliteconn.close() 
    if arg.mysql:
        mysqlconn.commit()
        mysqlconn.close()

    ## Close WebDriver
    driver.quit()
