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

0. Set the meeting name below
1. Select, then drag and drop all zoom activation emails from Apple Mail to a folder.  This will produce one .eml file
   per zoom activation email.

2. Pass that folder location as a parameter to this script. An optional 2nd parameter is the schedule.xlsx file from
   xlttozoom. If this file contains zoom_host_password  host_zoom_user_email and type fields, then these will be used
   rather than the hard coded defaults for the account password. The event type will used as the last name. 

The script will open each email, find the activation link url, open it in a browser, and set the password to the value
defined in teh zoompwd variable below.

Example:

./activate_zoom_accounts.py ~/Desktop/zoom_activation_emls_folder xltozoom/schedule.xlsx

"""

meeting_name = "MLSys 2021"
input(f"Using {meeting_name}: ")

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
from openpyxl import load_workbook

zoompwd = os.getenv("ZOOMPWD")

parser = ArgumentParser()
parser.add_argument("file", nargs="*", help="supply path to folder to collection of account activation .eml (emails dragged from Apple mail) files from zoom as first param. The 2nd param should be the scheudle xlsx that has zoom_host_password, host_zoom_user_email and type.")
ns = parser.parse_args()

emls = glob.glob(ns.file[0] + "/*.eml")
email_parser = BytesParser



def viewhtml(html):
    open("/tmp/delme.html", 'wb').write(html)
    os.system("open /tmp/delme.html")


data = {}

if len(ns.file) > 1:
    schedulexlsx = ns.file[1]

    wb = load_workbook(schedulexlsx)
    ws = wb.active
    
    headers = [i.value for i in ws[1] if i.value]

    for row in ws.iter_rows(min_row=2):

        row_data = dict(zip(headers, [i.value for i in row]))

        host_zoom_user_email = row_data.get("host_zoom_user_email")
        row_type = row_data.get("type")
        zoom_host_password =  row_data.get("zoom_host_password")
    
        if zoom_host_password and row_type and host_zoom_user_email:
            data[host_zoom_user_email] = {
                "zoom_host_password": zoom_host_password,
                "type": row_type,
                }
        else:
            print("skipping row {}".format(row_data))



default_password = "CubeVis31"
default_type = "Talk"

schedule_data = data

for eml in emls:

    fp = open(eml,'rb')
    msg = BytesParser().parse(fp)
    html = msg.get_payload(decode=True).decode("UTF-8")
    soup = bs(html, features="lxml")
    links = soup.findAll("a")
    login_email = soup.find("table").find("table").find("table").findAll("td")[0].text.strip().replace("Hello ", "").strip(",")
    print(login_email)
    schedulexlsx_info = schedule_data.get(login_email, {})

    Password = schedulexlsx_info.get("zoom_host_password", default_password)
    Lastname = schedulexlsx_info.get("type", default_type)


    #Exclude links that aren't activation links
    links = [link['href'] for link in links if "zoom.us/activate" in link['href']]
    #There may be more than one activation link; get only the first one. 

    if links:
        link = links[0]
        driver = webdriver.Firefox()
        driver.get(link)
        try:
            login = driver.find_element_by_link_text("Sign Up with a Password")
        except NoSuchElementException:
            print("{} has already been processed. Press c [enter] to continue".format(login_email))
            driver.close()
            continue
        print("Activating {} with {} and lastname of {}".format(login_email, Password, Lastname))
        login.click()
        firstname = driver.find_element_by_id("firstName")
        firstname.send_keys(meeting_name)
        lastname = driver.find_element_by_id("lastName")
        lastname.send_keys(Lastname)
        password = driver.find_element_by_id("password")
        password.send_keys(Password)
        cpassword = driver.find_element_by_id("confirm_password")
        cpassword.send_keys(Password)
        Continue = driver.find_element_by_link_text("Continue")
        Continue.click()
        driver.close()
        print("Activated {}".format(login_email))

        continue





