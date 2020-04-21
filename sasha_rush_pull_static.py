#!/usr/bin/env python

import os
import sys
import subprocess as sp
from pdb import set_trace as debug

if os.uname()[0] == "Darwin":
    os.chdir("/Users/lee/Sites/iclr_static2020")
else:
    os.chdir("/www/iclr_static2020")


result = sp.Popen(['git', 'pull'], stdout=sp.PIPE, stderr=sp.PIPE).communicate()
sys.exit(0)