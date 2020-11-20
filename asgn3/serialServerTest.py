
from datetime import datetime, time, timedelta
#from sanic_scheduler import SanicScheduler, task
from sanic import Sanic, response
from sanic.response import json
from sanic.handlers import ErrorHandler
from sanic.exceptions import NotFound
from requests.exceptions import Timeout
#from vectorclock import *
from VectorClocks import *
from random import *
import os
import socket
import copy
import requests
import asyncio
import re
import time
import json
from sanic.views import HTTPMethodView




def requestMaker():

    url     = "http://localhost:8082/key-value-store/"

    url1    = "http://localhost:8083/key-value-store/"

    url2    = "http://localhost:8084/key-value-store/"

    headers   = {'content-type':'application/json'}
    response  = ""
    causalMet = ""

    try:
        dat       = {"value": 122, "causal-metadata": causalMet}
        payload   = json.dumps(dat)
        response  = requests.put(url + "x", headers=headers, data=payload)
        dataDict  = response.json()
        causalMet = dataDict["causal-metadata"]
        print(dataDict)
    except requests.exceptions.ConnectionError:
        print("server is down.")

    print("This is causalMet between requests: " + str(causalMet))

    

    try:
        dat       = {"value": 67, "causal-metadata": causalMet}
        payload   = json.dumps(dat)
        response  = requests.put(url1 + "x", headers=headers, data=payload)
        dataDict  = response.json()
        causalMet = dataDict["causal-metadata"]
        print(dataDict)
    except requests.exceptions.ConnectionError:
        print("server is down.")

    try:
        #dat       = {"value": 122, "causal-metadata": causalMet}
        payload   = json.dumps(dat)
        response  = requests.get(url + "x", headers=headers, data=payload)
        dataDict  = response.json()
        causalMet = dataDict["causal-metadata"]
        print(dataDict)
    except requests.exceptions.ConnectionError:
        print("server is down.")

        


def main():

    requestMaker()

if __name__ == '__main__':
    main()