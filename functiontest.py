import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from enum import Enum
import os
import logging
#from seqrlogin import login
from zapv2 import ZAPv2

from dotenv import load_dotenv

from scan import pullReport

logging.warning('is this on?')
proxy="http://127.0.0.1:8081"
#domain="dsm-staging.datadonationplatform.org"
load_dotenv("test.env")

zap = ZAPv2(proxies={"http": proxy, "https": proxy})
site="ddp"
template="traditional-xml"
context="angio.staging.datadonationplatform.org"
url="https://angio.staging.datadonationplatform.org"

zap.spider.scan_as_user(2, 22, url)
time.sleep(5)    
while (zap.spider.status == "running"):
    time.sleep(5)


# zap.script.set_global_var("token_auth.js","token",token)
#print(os.getenv("DDP_USER"))