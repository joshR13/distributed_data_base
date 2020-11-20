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

app       = Sanic("asgn3_2.py")
scheduler = SanicScheduler(app)

env_variables = dict(os.environ)
viewString    = env_variables['VIEW']
viewList      = viewString.split(",") #viewList = servers in cluster that are visible (this is the one that gets edited.)
viewListCopy  = copy.deepcopy(viewList) #viewListCopy = total number of servers in cluster (this is the one that is used as loop control variable)

data = {}
retrievedDataStore = {}

vectorClock = VectorClocks(viewListCopy)

async def notify_other_instances(flag, dataVersion, key):

    VCMax = ""

    for x in range(len(viewListCopy)):

        headers = {'content-type':'application/json'}

        url      = "http://" + str(viewListCopy[x]) + "/key-value-store-view/"
        url2     = "http://" + str(viewListCopy[x]) + "/dataStoreDispersal"
        contAddr = str(os.environ['SOCKET_ADDRESS'])

        #print("This is os.environ['SOCKET_ADDRESS']: " + os.environ['SOCKET_ADDRESS'] + "\n")

        if (str(viewListCopy[x]) != contAddr):

            if(flag == 0):
                try:
                    payload  = json.dumps({'socket-address':str(os.environ['SOCKET_ADDRESS'])})
                    response = requests.put(url, headers=headers, data=payload, timeout=3)

                    dat      = response.json()
                    store    = dat['store']
                    VC       = dat['vectorclock']

                    data.update(store)
                    vectorClock.updateVC(VC) #this section of code will only executed upon startup of replica
                                             #so we don't need to worry about more complicated checks
                except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
                    viewAddr = viewListCopy[x]
                    if(viewAddr in viewList):
                        viewList.remove(viewAddr)
                    print("server " + str(viewListCopy[x]) + " is down or timed out.")
                
            
            #Get dat data and store dat data.

            currentVecClock = vectorClock.returnVC()

            if(flag == 1):

                #this section of the code gets executed when the local replica has received a write request
                # with a version of the data that is more recent than what this local replica has stored.
                # Because of this, the local replica must try to update its own store before sending an ack
                # back to the client.


                try:
                    
                    response           = requests.get(url2, headers=headers, timeout=3)
                    store    = response.json['store']
                    vcUpdate = response.json['vectorclock']

                    if currentVecClock["vcvalue"] < vcUpdate["vcvalue"]: #If this replica's version of the store is behind
                                                                        # the version of the store that is being retrieved from
                                                                        # another replica, update the store of this replica
                                                                        # as well as the vector clock of this replica
                                                                        # with the store and vector clock of the other replica
                                                                        # that has just responded.

                        data.clear()               
                        data.update(retrievedDataStore)
                        vectorClock.incrementVC(vcUpdate["key"], vcUpdate["value"], vcUpdate["vcvalue"])

                except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
                    viewAddr = viewListCopy[x]
                    if(viewAddr not in viewList):
                        viewList.remove(viewAddr)
                    print("server " + str(viewList[x]) + " is down or timed out.")

        await asyncio.sleep(0.01)    
                    
async def updateOtherInstances(value, key, dataVersion):

    
    kvDict = {}
    kvDict.update({"key":str(key), "value":value, "version": dataVersion, "vectorclock":vectorClock.returnVC()})

    for x in range(len(viewListCopy)):
        url     = "http://" + str(viewListCopy[x]) + "/dataStoreDispersal"
        headers = {'content-type':'application/json'}

        if (str(viewListCopy[x]) != str(os.environ['SOCKET_ADDRESS'])):
            try:
                payload   = json.dumps(kvDict)#so kvDict now has all the necessary information to update the
                                              # other instances' data store as well as vector clock
                response = requests.put(url, headers=headers, data=payload, timeout=3)
            except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
                if(viewListCopy[x] in viewList):
                    addrToBeDeletedFromView = str(viewListCopy[x])
                    viewList.remove(addrToBeDeletedFromView)

        await asyncio.sleep(0.01)


@task(timedelta(seconds=30),timedelta(seconds=60))
async def scheduledUpdateSender(_):

    headers    = {'content-type':'application/json'}
    VC         = vectorClock.returnVC()
    dataDict   = {"vectorclock": VC, "store": data}
    payload    = json.dumps(dataDict)

    for x in range(len(viewListCopy)):

        url       = "http://" + str(viewListCopy[x]) + "/receive_update"
        viewAddr  = viewListCopy[x]
        localAddr = str(os.environ['SOCKET_ADDRESS'])

        if(viewAddr != localAddr):
        
            try:
                response = requests.put(url, headers=headers, data=payload, timeout=1.5)
                if(viewAddr not in viewList):
                    viewList.append(viewAddr)
            except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
                if(viewAddr in viewList):
                    viewList.remove(viewAddr)
        
        await asyncio.sleep(0.01)




@app.listener("before_server_start")
async def do_startup(app, loop):

    await notify_other_instances(0, "dummy")



class scheduledUpdate(HTTPMethodView):

    async def put(self, request):

        requestVc      = request.json['vectorclock']
        localVc        = vectorClock.returnVc()
        requestVcValue = requestVc['vcvalue']
        localVcValue   = localVc['vcvalue']
        requestStore   = request.json['store']

        if(localVcValue < requestVcValue):
            vectorClock.incrementVC(requestVc['key'], requestVc['value'], requestVcValue)
            data.clear()
            data.update(requestStore)
        
        return response.json({"message": "Update tasks completed."}, status=200)


class dataDisperse(HTTPMethodView):

    async def get(self, request): #accepts get request from other replica and returns this replica's data store
                                  #as well as vector clock structure.
        dispersal   = {}
        vecClock    = vectorClock.returnVC()
        dispersal.update({"store":data, "vectorclock":vecClock})
        return response.json(dispersal)

    async def put(self, request): #accepts put request from other replica, and updates this replica's
                                  #data store as well as vector clock with the json data contained in PUT request.
                                  
        ki       = request.json['key']
        val      = request.json['value']
        vecClock = request.json['vectorclock']
        version  = request.json['version']
        data.update({ki:{"value": val, "version": version }})
        vectorClock.incrementVC(ki, val, vecClock['vcvalue'] )

        return response.json({"message":"data store updated"}, status=200)

class viewOps(HTTPMethodView):

    async def get(self, request):

        initString = ", "

        returnString = initString.join(viewList)

        return response.json({"message":"View retrieved successfully","view":returnString})


    async def put(self, request):
        

        addrToBeAppendedToView = request.json['socket-address']
        VC = vectorClock.returnVC()
        if (addrToBeAppendedToView in viewList):
            return response.json({"error":"Socket address already exists in the view","message":"Error in PUT", "vectorclock":VC, "store":data}, status=404)

        elif (addrToBeAppendedToView not in viewList):
            viewList.append(addrToBeAppendedToView)
            return response.json({"message":"Replica added successfully to the view", "vectorclock":VC, "store":data}, status=201)


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
        version = 0

        if (clientCm == ""):

            version      = 0
            localVC      = returnVC()
            localAddr    = str(os.environ['SOCKET_ADDRESS'])
            localVcValue = localVC[localAddr]
            updateVal    = localVcValue +  1
            if key not in data:
                version = 1
            if key in data:
                keyData     = data[str(key)]
                dataVersion = keyData['version']
                version     = dataVersion + 1 
            data.update({str(key):{"value": dat, "version": version}})
            vectorClock.updateVC(str(key), dat, version)

        if (clientCm != ""):

            dataKey = data[str(key)]
            version = dataKey["version"]

            if (clientCm["vcvalue"] > serverCm["vcvalue"]):

                await notify_other_instances(1, )

            data.update({str(key):{"value": dat, "version": version + 1 }})
            vectorClock.incrementVC(str(key), dat, clientCm["vcvalue"] + 1)

            #IMPLEMENT YOUR CAUSAL CONSISTENCY LOGIC HERE!
        
        
        #await asyncio.wait([updateOtherInstances(data[str(key)], key)])
        keyData = data[str(key)]
        await updateOtherInstances(keyData['value'], key, version)

        return response.json({"message":"Added successfully", "causal-metadata": {"vector_clock": vectorClock.returnVC(), "value": dat, "key": key, "version": version}}, status=200)
    
    async def get(self, request, key):

        print("Here is the data store from the GET case: " + str(data))

        #vectorClock.incrementVC()
        #print(vectorClock.returnVC())

        #{"message":"Retrieved successfully", "causal-metadata": "<V2>", "value": 2}

        if key not in data.keys():

            return response.json({"message": "Key does not exist.  Check validity of key or try again later."}, status=200)

        else:

            await notify_other_instances(1, "dummy")

            vc      = vectorClock.returnVC()
            keyData = data[str(key)] 


            return response.json({"message":"Retrieved successfully", "causal-metadata": {"vector_clock": vc, "version": keyData['version']} , "value": keyData['value']}, status=200)

    async def delete(self, request, key):

        return response.json(vectorClock.returnVC())

        

    

        


app.add_route(dataDisperse.as_view(), '/dataStoreDispersal')
app.add_route(scheduledUpdate.as_view(), '/receive_update')
app.add_route(viewOps.as_view(), '/key-value-store-view')
app.add_route(dataOps.as_view(), '/key-value-store/<key>')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8085)
