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
from sanic.views import HTTPMethodView

app = Sanic("asgn3_2.py")

env_variables = dict(os.environ)
viewString    = env_variables['VIEW']
viewList      = viewString.split(",")
viewListCopy  = viewList

data = {}
retrievedDataStore = {}

vectorClock = VectorClocks()

#print(vectorClock.returnVC())
#vectorClock.incrementVC()
#print(vectorClock.returnVC())

async def notify_other_instances(flag):
    for x in range(len(viewList)):

        

        headers = {'content-type':'application/json'}

        url  = "http://" + str(viewList[x]) + "/key-value-store-view/"
        url2 = "http://" + str(viewList[x]) + "/dataStoreDispersal"

        print("This is viewList[x]: " + viewList[x] + "\n")
        #print("This is os.environ['SOCKET_ADDRESS']: " + os.environ['SOCKET_ADDRESS'] + "\n")

        if (str(viewList[x]) != str(os.environ['SOCKET_ADDRESS'])):

            if(flag == 0):
                try:
                    payload  = json.dumps({'socket-address':str(os.environ['SOCKET_ADDRESS'])})
                    response = requests.put(url, headers = headers, data=payload)
                    #print("THIS IS RESPONSE: " + str(response))
                except requests.exceptions.ConnectionError:
                    print("server " + str(viewList[x]) + " is down.  FARGLES")
            
            #Get dat data and store dat data.

            currentVecClock = vectorClock.returnVC()


            try:
                
                response           = requests.get(url2, headers = headers)
                #print("This is the json() from the response: " + response.json())
                dictData           = response.json()
                retrievedDataStore = dictData["store"]
                vcUpdate           = dictData["vectorClock"]

                if currentVecClock["vcvalue"] < vcUpdate["vcvalue"]: #If this replica's version of the store is behind
                                                                     # the version of the store that is being retrieved from
                                                                     # another replica, update the store of this replica
                                                                     # as well as the vector clock of this replica
                                                                     # with the store and vector clock of the other replica
                                                                     # that has just responded.

                    data.clear()               
                    data.update(retrievedDataStore)
                    vectorClock.incrementVC(vcUpdate["key"], vcUpdate["value"], vcUpdate["vcvalue"])

            except requests.exceptions.ConnectionError:
                print("server " + str(viewList[x]) + " is down.")





async def updateOtherInstances(value, key):

    
    kvDict = {}
    kvDict.update({"key":str(key), "value":value, "vectorclock":vectorClock.returnVC()})

    for x in range(len(viewList)):
        url     = "http://" + str(viewList[x]) + "/dataStoreDispersal"
        headers = {'content-type':'application/json'}

        if (str(viewList[x]) != str(os.environ['SOCKET_ADDRESS'])):
            try:
                payload   = json.dumps(kvDict)#so kvDict now has all the necessary information to update the
                                              # other instances' data store as well as vector clock
                response = requests.put(url, headers=headers, data=payload)
            except requests.exceptions.ConnectionError:
                print("server " + str(viewList[x]) + " is down.")




@app.listener("before_server_start")
async def do_startup(app, loop):
    try:
        await notify_other_instances(0)
    except requests.exceptions.ConnectionError:
        print("Server is down")

#@app.middleware('request')
#async def simulUpdate(request):

    #REMEMBER!  You may have to add in some checks for stupid shit regarding the key here as well as below 
    # in the PUT function itself.

#    if ("/key-value-store/" in request.url):

#        urlStr      = str(request.url)
#        urlStrSplit = urlStr.split("/")
#        key         = urlStrSplit[len(urlStrSplit) - 1]

#        if(request.method == "PUT"):
        
#            dat      = request.json['value']
#            clientCm = request.json['causal-metadata']
#            serverCm = vectorClock.returnVC()

#            if (clientCm == ""):
#                print("Hello from inside empty string case!")

#                data.update({str(key):dat})
#                vectorClock.incrementVC(str(key), dat, 1)

#            if (clientCm != ""):

#                if (clientCm["vcvalue"] > serverCm["vcvalue"]):

#                    await notify_other_instances(1)

#                data.update({str(key):dat})
#                vectorClock.incrementVC(str(key), dat, clientCm["vcvalue"] + 1)

#            await updateOtherInstances(dat, key)
            

class dataDisperse(HTTPMethodView):

    async def get(self, request): #accepts get request from other replica and returns this replica's data store
                                  #as well as vector clock structure.

        dispersal   = {}
        vecClock    = vectorClock.returnVC()
        dataStorage = data.copy()
        dispersal.update({"store":data, "vectorClock":vecClock})
        #return response.json(json.dumps(dispersal))
        return response.json(dispersal)

    async def put(self, request): #accepts put request from other replica, and updates this replica's
                                  #data store as well as vector clock with the json data contained in PUT request.
                                  
        ki       = request.json['key']
        val      = request.json['value']
        vecClock = request.json['vectorclock']
        data.update({ki:val})
        vectorClock.incrementVC(ki, val, vecClock['vcvalue'] )

        return response.json({"message":"data store updated"}, status=200)

class viewOps(HTTPMethodView):

    async def get(self, request):

        initString = ", "

        returnString = initString.join(viewList)

        return response.json({"message":"View retrieved successfully","view":returnString})


    async def put(self, request):

        addrToBeAppendedToView = request.json['socket-address']

        if (addrToBeAppendedToView in viewList):
            return response.json({"error":"Socket address already exists in the view","message":"Error in PUT"}, status=404)

        elif (addrToBeAppendedToView not in viewList):
            viewList.append(addrToBeAppendedToView)
            return response.json({"message":"Replica added successfully to the view"}, status=201)


    async def delete(self, request):

        addrToBeDeletedFromView = request.json['socket-address']
        print("THis is from DELETE: " + str(addrToBeDeletedFromView))
        try:
            viewList.remove(addrToBeDeletedFromView)
        except:
            return response.json({"error":"Socket address does not exist in the view","message":"Error in DELETE"}, status=404)
            
        return response.json({"message":"Replica deleted successfully from the view"})

class dataOps(HTTPMethodView):

    async def put(self, request, key):

    

        #return response.json({"message":"Added successfully", "causal-metadata": vectorClock.returnVC()}, status=200)

        dat      = request.json['value']
        clientCm = request.json['causal-metadata']
        serverCm = vectorClock.returnVC()

        if (clientCm == ""):

            data.update({str(key):dat})
            vectorClock.incrementVC(str(key), dat, 1)

        if (clientCm != ""):

            if (clientCm["vcvalue"] > serverCm["vcvalue"]):

                await notify_other_instances(1)

            data.update({str(key):dat})
            vectorClock.incrementVC(str(key), dat, clientCm["vcvalue"] + 1)

            #IMPLEMENT YOUR CAUSAL CONSISTENCY LOGIC HERE!
        
        
        #await asyncio.wait([updateOtherInstances(data[str(key)], key)])
        await updateOtherInstances(data[str(key)], key)

        return response.json({"message":"Added successfully", "causal-metadata": vectorClock.returnVC()}, status=200)
    
    async def get(self, request, key):

        #vectorClock.incrementVC()
        #print(vectorClock.returnVC())

        #{"message":"Retrieved successfully", "causal-metadata": "<V2>", "value": 2}

        if key not in data.keys():

            return response.json({"message": "Key does not exist.  Check validity of key or try again later."}, status=200)

        else:

            await notify_other_instances(1)

            vc    = vectorClock.returnVC()
            value = data[str(key)] 

            return response.json({"message":"Retrieved successfully", "causal-metadata": vc, "value": value}, status=200)

    async def delete(self, request, key):

        return response.json(vectorClock.returnVC())

    

        


app.add_route(dataDisperse.as_view(), '/dataStoreDispersal')
app.add_route(viewOps.as_view(), '/key-value-store-view')
app.add_route(dataOps.as_view(), '/key-value-store/<key>')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8085)
