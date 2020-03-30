#!/usr/bin/env python

import pytz
from pdb import set_trace as debug
from argparse import ArgumentParser
from openpyxl import load_workbook
from create_or_update_zoom import create_or_update_zoom
import os
import sys


parser = ArgumentParser()
parser.add_argument("--clearAll", action="store_true", help="delete all meetings listed in schedule.xlsx")
parser.add_argument("--users", action="store_true")
parser.add_argument("--file", default="schedule.xlsx")
ns = parser.parse_args()

UTC = pytz.timezone("UTC")

my_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(my_dir, "zoomus"))

wb = load_workbook(ns.file)
ws = wb.active

dirty = False

headers = [item.value for item in ws[1]]

for row in ws.iter_rows(min_row=2):
    data = dict(zip(headers, [item.value for item in row]))
    integration = data.get("integration")
    if integration in ["Zoom", None]:
        result = create_or_update_zoom(data)
        print("{0}: {1}".format(result.get("action").capitalize(), result.get("topic")))
        if result.get("action") == "created":
            zoomid = row[headers.index("zoomid")]
            zoomid.value = result.get("id")
            dirty = True
        debug()


if dirty:
    from tkinter import messagebox
    
    
    messagebox.showinfo("Warning","{} has been updated. Please reopen it without saving.".format(ns.filenmae))



