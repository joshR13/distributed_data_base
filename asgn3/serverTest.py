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

cm       = ""
response = ""
count    = 0

async def requestSender(requestType, addr, key, causalMet):

    headers = {'content-type':'application/json'}
    url     = addr + key
    dat     = causalMet

    if(requestType == "p"):

        try:

            payload  = json.dumps(dat)
            response = requests.put(url, headers=headers, data=payload)
            print(response.json())  
            #cm = data["causal-metadata"]["vcvalue"] 
        except requests.exceptions.ConnectionError:
            print(requestType + "server is down.")

    if(requestType == "g"):

        try:
            response = requests.get(url, headers=headers)
            print(response.json())
        except requests.exception.ConnectionError:
            print(requestType + "server is down.")     
    



async def putRequest(key, addr):

    backupCm = cm

    dat     = {"value": 122, "causal-metadata": cm}

    await requestSender("p", addr, key, dat)

    if ( (isinstance(cm, int) == True) and (cm[vcvalue] < backupCm) ):
        print("Error." + cm[vcvalue] + " < " + backupCm)
    else:
        print("All good.")

async def getRequest(key, addr):

    backupCm = cm
    dummy    = {}

    await requestSender("g", addr, key, dummy)

    if ( (isinstance(cm, int) == True) and (cm[vcvalue] < backupCm) ):
        print("Error." + cm[vcvalue] + " < " + backupCm)
    else:
        print("All good.")


    

    

        
    #try:
    #    payload = json.dumps(dat)#so kvDict now has all the necessary information to update the
                                        # other instances' data store as well as vector clock
    #    response = requests.put(url, headers=headers, data=payload)
    #except requests.exceptions.ConnectionError:
    #    print("server 8082 is down.")








async def main():

    url     = "http://localhost:8082/key-value-store/"

    url1    = "http://localhost:8083/key-value-store/"

    url2    = "http://localhost:8084/key-value-store/"

    await asyncio.wait([putRequest("x", url), getRequest("x", url), putRequest("x", url1), getRequest("x", url2)])

    

#if __name__ == '__main__':
#    main()

loop =asyncio.get_event_loop()
loop.run_until_complete(main())