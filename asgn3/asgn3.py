from datetime import datetime, time, timedelta
from sanic_scheduler import SanicScheduler, task
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


app = Sanic("asgn3.py")
env_variables = dict(os.environ)
viewString    = env_variables['VIEW']
viewList      = viewString.split(",")
viewListCopy  = viewList
#viewDict      = {k.strip():v.strip() for k,v in (pair.split(':') for pair in viewList)}


data = {'dingus':'bungus'}
retrievedDataStore = {}

vectorClock = VectorClocks()



for x in range(len(viewList)):



    headers = {'content-type':'application/json'}

    url  = "http://" + str(viewList[x]) + "/key-value-store-view/"
    url2 = "http://" + str(viewList[x]) + "/dataStoreDispersal"

    print("This is viewList[x]: " + viewList[x] + "\n")
    print("This is os.environ['SOCKET_ADDRESS']: " + os.environ['SOCKET_ADDRESS'] + "\n")

    if (str(viewList[x]) != str(os.environ['SOCKET_ADDRESS'])):
        try:
            payload  = json.dumps({'socket-address':str(os.environ['SOCKET_ADDRESS'])})
            response = requests.put(url, headers = headers, data=payload)
            print("THIS IS RESPONSE: " + str(response))
        except requests.exceptions.ConnectionError:
            print("server " + str(viewList[x]) + " is down.")
        
        #Get dat data and store dat data.

        try:
            
            response           = requests.get(url2, headers = headers)
            print("This is the json() from the response: " + response.json())
            retrievedDataStore = response.json()
            data               = retrievedDataStore
        except requests.exceptions.ConnectionError:
            print("server " + str(viewList[x]) + " is down.")
        #print(retrievedDataStore)

    
    
#return entire data store to any inquiring replica    
@app.route('/dataStoreDispersal', methods=["GET"])
async def index(request):


    return response.json(json.dumps(data))
    
    


@app.route('/key-value-store-view', methods=["GET", "PUT", "DELETE"])
async def index(request):
    #return respon.json({'message': 'Welcome to Die!'})

    if request.method == "GET":
        initString = ", "

        returnString = initString.join(viewList)

        return response.json({"message":"View retrieved successfully","view":returnString})
    
    if request.method == "DELETE":

        addrToBeDeletedFromView = request.json['socket-address']
        print("THis is from DELETE: " + str(addrToBeDeletedFromView))
        try:
            viewList.remove(addrToBeDeletedFromView)
        except:
            return response.json({"error":"Socket address does not exist in the view","message":"Error in DELETE"}, status=404)
            
        return response.json({"message":"Replica deleted successfully from the view"})
        

    if request.method == "PUT":
        print("PUT has been hit.")

        addrToBeAppendedToView = request.json['socket-address']

        if (addrToBeAppendedToView in viewList):
            return response.json({"error":"Socket address already exists in the view","message":"Error in PUT"}, status=404)

        elif (addrToBeAppendedToView not in viewList):
            viewList.append(addrToBeAppendedToView)
            return response.json({"message":"Replica added successfully to the view"}, status=201)

           

@app.route('/key-value-store/<key>', methods=["GET", "PUT", "DELETE"])
async def index(key):

    

        
    return response.text(key)
    

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8085)