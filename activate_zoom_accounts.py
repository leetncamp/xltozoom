#!/usr/bin/env python
# encoding: utf-8

"""

This script requires MacOS and Apple Mail to work without modification.  When creating one zoom account per person, you
will need to create 2000 accounts (NeurIPS) and manually activate them.   This script helps automate that will selenium
driver.

pip install selenium

There are more installation steps required as documented here:
https://selenium-python.readthedocs.io/getting-started.html

This script is set up to use the Gecko Driver and Firefox, but can be easily modified to use another browser.  Safari on
MacOS includes a selenium driver and works without much fuss.  To use this script:

1. Select, then drag and drop all zoom activation emails from Apple Mail to a folder.  This will produce one .eml file
   per zoom activation email.

2. Pass that folder location as a parameter to this script.

The script will open each email, find the activation link url, open it in a browser, and set the password to the value
defined in teh zoompwd variable below.

"""


import os
import sys
from pdb import set_trace as debug
stop = debug
import glob
from argparse import ArgumentParser
from email.parser import BytesParser
import email
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

driver = webdriver.Firefox()
zoompwd = os.getenv("ZOOMPWD")

parser = ArgumentParser()
parser.add_argument("file", help="supply folder to collection of acount activation .eml (emails dragged from Apple mail) files from zoom")
ns = parser.parse_args()

emls = glob.glob(ns.file + "/*.eml")
email_parser = BytesParser



def viewhtml(html):
    open("/tmp/delme.html", 'wb').write(html)
    os.system("open /tmp/delme.html")




for eml in emls:
    fp = open(eml,'rb')
    msg = BytesParser().parse(fp)
    html = msg.get_payload(decode=True).decode("UTF-8")
    soup = bs(html, features="lxml")
    links = soup.findAll("a")
    login_email = soup.find("table").find("table").find("table").findAll("td")[0].text.strip().replace("Hello ", "").strip(",")
    print(login_email)
    
    #Exclude links that aren't activation links
    links = [link['href'] for link in links if link['href'].startswith("https://zoom.us.activate")]
    #There may be more than one activation link; get only the first one. 
    if links:
        link = links[0]
        driver = webdriver.Firefox()
        driver.get(link['href'])
        try:
            login = driver.find_element_by_link_text("Sign Up with a Password")
        except NoSuchElementException:
            print("{} has already been processed. Press c [enter] to continue".format(login_email))
            driver.close()
            continue

        login.click()
        firstname = driver.find_element_by_id("firstName")
        firstname.send_keys("NeurIPS 2020")
        lastname = driver.find_element_by_id("lastName")
        lastname.send_keys("Poster")
        password = driver.find_element_by_id("password")
        password.send_keys("FernCube31")
        cpassword = driver.find_element_by_id("confirm_password")
        cpassword.send_keys("FernCube31")
        Continue = driver.find_element_by_link_text("Continue")
        Continue.click()
        driver.close()
        print("Activated {}".format(login_email))
        continue





