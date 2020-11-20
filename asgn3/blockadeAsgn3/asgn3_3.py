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

app = Sanic("asgn3_3.py")

env_variables     = dict(os.environ)
viewString        = env_variables['VIEW']
viewList          = viewString.split(",")
viewListCopy      = copy.deepcopy(viewList)

identifierNumDict = {}
for x in range(len(viewListCopy)):
    identifierNumDict.update( {str(viewListCopy[x]):x} )
    
print("Here's identiferNumDict: " + str(identifierNumDict) )

################################################################
#this block is for update logic testing.
vcValueString = env_variables['VCVALUES']
vcValueList   = vcValueString.split(",")

print("Here's vcValueList: " + str(vcValueList))
################################################################

data = {}
retrievedDataStore = {}

vectorClock = VectorClocks(viewListCopy)

################################################################
#this block is also for update logic testing.

for x in range( len(viewListCopy) ):
    vectorClock.updateVC( str(viewListCopy[x]), int(vcValueList[x]) )

localTestingVC = vectorClock.returnVC()
print("Here's the localVC after the environment values have been inserted: " + str(localTestingVC) )
################################################################

async def notifyOtherInstances():
    for x in range(len(viewListCopy)):

        headers      = {'content-type':'application/json'}
        localAddress = str(os.environ['SOCKET_ADDRESS'])

        #url  = "http://" + str(viewList[x]) + "/key-value-store-view/"
        url = "http://" + str(viewListCopy[x]) + "/dataStoreDispersal"

        if(str(viewListCopy[x]) != localAddress):

            try:
                
                payload       = json.dumps({'localAddress': localAddress})
                response      = requests.get(url, headers=headers, data=payload, timeout=5)
                responseData  = response.json()
                incomingStore = responseData['store']
                incomingVC    = responseData['vectorclock']
                localVC       = vectorClock.returnVC()
                verdict       = vectorClock.VcComparator(localVC, incomingVC)

                if(verdict == "<"):

                    vectorClock.replaceVC(incomingVC)
                    data.clear()
                    data.update(incomingStore)
            
            except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:

                print("server " + str(viewListCopy[x]) + "is down.")

                viewList.remove(viewListCopy[x])

        #await asyncio.sleep(0.01)




async def updateOtherInstances(dataDict):

    print("Hello from updateOtherInstances!")

    updateDict = {}
    key        = dataDict['key']
    value      = dataDict['value']
    version    = dataDict['version']
    localVC    = vectorClock.returnVC()
    localIdNum = identifierNumDict[str(os.environ['SOCKET_ADDRESS'])]
    updateDict.update({'key':key, 'value':value, 'causal-metadata':{'vectorclock':localVC, 'version':version, 'localIdNum':localIdNum}})
    payload    = json.dumps(updateDict)
    
    
    headers      = {'content-type':'application/json'}
    localAddress = str(os.environ['SOCKET_ADDRESS'])

    for x in range(len(viewListCopy)):

        url = "http://" + str(viewListCopy[x]) + "/dataStoreDispersal" 

        if(str(viewListCopy[x]) != localAddress):
        
            #await asyncio.sleep(0.01)

            try:
                requests.put(url, headers=headers, data=payload, timeout=5)
            except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
                if(viewListCopy[x] in viewList):
                    print("From " + localAddress + " updateOtherInstances funct: server " + str(viewListCopy[x]) + " is down or timed out.")
                    viewList.remove(viewListCopy[x])
       
        #await asyncio.sleep(0.01)


@app.listener("before_server_start")
async def do_startup(app, loop):
    await notifyOtherInstances()

async def contactSingleInstance(addr, key):

    headers = {'content-type':'application/json'}

    url = "http://" + str(addr) + "/key-value-store/" + str(key)

    try:
        response = requests.get(url, headers=header, timeout=5)

        if(response.status_code == 200):

            responseData    = response.json()
            responseValue   = responseData['value']
            responseCM      = response['causal-metadata']
            responseVC      = responseCM['vectorclock']
            responseVersion = responseCM['version']

            vectorClock.updateVCDelivery(responseVC)
            data.update({str(key):{'value':responseValue, 'version':responseVersion}})

    except(requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
        if(str(addr) in viewList):
            viewList.remove(str(addr))


class dataDisperse(HTTPMethodView):

    async def get(self, request):

        incomingAddress = request.json['localAddress']
        if(str(incomingAddress) not in viewList):
            viewList.append(incomingAddress)

        localVC  = vectorClock.returnVC()
        dataDict = {'store': data, 'vectorclock': localVC}

        return response.json(dataDict) 

    async def put(self, request):
        
        key             = request.json['key']
        incomingValue   = request.json['value']

        incomingCM      = request.json['causal-metadata']
        incomingID      = incomingCM['localIdNum']
        incomingVersion = incomingCM['version']
        incomingVC      = incomingCM['vectorclock']
        localVC         = vectorClock.returnVC()
        localAddress    = str(os.environ['SOCKET_ADDRESS'])
        

        if(vectorClock.VcComparator(incomingVC, localVC) == ">"):

            print("Hello from dataDisperse greater than case!")

            data.update({str(key):{'value':incomingValue, 'version':incomingVersion}})
            vectorClock.replaceVC(incomingVC)

        if(vectorClock.VcComparator(incomingVC, localVC) == "||"):


            if(key in data):

                print("Hello from dataDisperse 'key in data' case!!")

                localKeyData    = data[str(key)]
                localVersion    = localKeyData['version']
                localValue      = localKeyData['value']
                localKeyId      = localKeyData['ID']

                if(incomingVersion > localVersion):
                    data.update({str(key):{'value':incomingValue, 'version':incomingVersion}}) 
                if(incomingVersion < localVersion):
                    data.update({str(key):{'value':localValue, 'version':localVersion}})
                if(incomingVersion == localVersion):
                    if(incomingID > localKeyId):
                        data.update({str(key):{'value':incomingValue, 'version':incomingVersion, 'ID':incomingID}})
                    if(incomingID < localKeyId):
                        data.update({str(key):{'value':localValue, 'version':localVersion, 'ID':localKeyId}})

            if(key not in data):

                data.update({str(key):{'value':incomingValue, 'version':incomingVersion, 'ID':incomingID}})

            vectorClock.updateVCDelivery(incomingVC)
        
        return response.json({"message":"Update handled."}, status=200)
                

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
        try:
            viewList.remove(addrToBeDeletedFromView)
        except:
            return response.json({"error":"Socket address does not exist in the view","message":"Error in DELETE"}, status=404)
            
        return response.json({"message":"Replica deleted successfully from the view"})

class dataOps(HTTPMethodView):

    async def put(self, request, key):

        print("Hello from dataOps PUT case!")
        
        updateDict   = {}
        value        = request.json['value']
        localVC      = vectorClock.returnVC()
        localAddress = str(os.environ['SOCKET_ADDRESS'])
        localID      = identifierNumDict[localAddress]
        #localVcValue = localVC[localAddress] + 1

        if(request.json['causal-metadata'] == ""):


            if(str(key) in data):

                keyData           = data[str(key)]
                localVersion      = keyData['version']
                updatedVersionNum = localVersion + 1
                dataDict          = {str(key): {'value': str(value), 'version': updatedVersionNum, 'ID':localID}}
                data.update(dataDict)
                updatedVcValue    = localVC[localAddress] + 1
                vectorClock.updateVC(localAddress, updatedVcValue)
                updateDict.update({'key':str(key), 'value':value, 'version':updatedVersionNum})

            
            if(str(key) not in data):
                
                dataDict       = {str(key): {'value': str(value), 'version': 1, 'ID':localID}}
                data.update(dataDict)
                updatedVcValue = localVC[localAddress] + 1
                vectorClock.updateVC(localAddress, updatedVcValue)
                updateDict.update({'key':str(key), 'value':value, 'version':1})

            
            await updateOtherInstances(updateDict)

            VC           = vectorClock.returnVC()
            keyData      = data[str(key)]
            version      = keyData['version']
            localAddress = str(os.environ['SOCKET_ADDRESS'])  

            return response.json({"message":"Added successfully", "causal-metadata": {'vectorclock':VC, 'key':key, 'version':version, 'last_addr_contacted':localAddress}}, status=200)

        if(request.json['causal-metadata'] != ""):

            incomingValue     = request.json['value']
            clientCM          = request.json['causal-metadata']
            clientVC          = clientCM['vectorclock']
            localVC           = vectorClock.returnVC()
            clientCmKey       = clientCM['key']
            clientCmVersion   = clientCM['version']
            lastAddrContacted = clientCM['last_addr_contacted']
            localAddress      = str(os.environ['SOCKET_ADDRESS'])

            if( (vectorClock.VcComparator(clientVC, localVC) == "<") or (vectorClock.VcComparator(clientVC, localVC) == "=") ): #This means all is as it should be
                print("Hello from 'clientVC < localVC or clientVC == localVC' case in dataOps PUT case!")
                if(str(key) in data):

                    localKeyData      = data[str(key)]
                    updatedVersionNum = localKeyData['version'] + 1 
                    data.update({str(key):{'value':incomingValue, 'version':updatedVersionNum, 'ID':localID}})

                if(str(key) not in data):

                    data.update({str(key):{'value':incomingValue, 'version':1, 'ID':localID}})
                
                localVC           = vectorClock.returnVC()
                updatedLocalVcVal = localVC[localAddress] + 1
                localVC           = vectorClock.returnVC()
                keyData           = data[str(key)]
                localVersion      = keyData['version']
                localValue        = keyData['value']

                vectorClock.updateVC(localAddress, updatedLocalVcVal)
                updateDict.update({'key':str(key), 'value':localValue, 'version':localVersion})

                await updateOtherInstances(updateDict)

                return response.json({"message":"Added successfully", "causal-metadata": {'vectorclock':localVC, 'key':str(key), 'version':localVersion, 'last_addr_contacted':localAddress}}, status=200)
            
            if( (vectorClock.VcComparator(clientVC, localVC) == ">") or (vectorClock.VcComparator(clientVC, localVC) == "||") ):#This means that the local replica is missing some writes
                
                localCmKeyData = ""
                if(clientCmKey in data):
                    localCmKeyData = data[str(clientCmKey)]

                if( (clientCmKey not in data) or ( (clientCmKey in data) and (localCmKeyData['version'] < clientCmVersion) ) ):

                    if( (str(key) in data) and (clientCmKey == str(key)) ):#if the key is in the store, then we know that
                                                                           #the second half of the above if statement must be
                                                                           #true; i.e., the local version of the key is less than
                                                                           #the incoming version.  Therefore we want to increment
                                                                           #the incoming version, and use that value as the new version
                                                                           #number.
                        data.update({str(key):{'value':incomingValue, 'version':incomingVersion + 1, 'ID':localID}})

                    if( (str(key) in  data) and (clientCmKey != str(key)) ):
                        data.update({str(key):{'value':incomingValue, 'version':localCmKeyData['version'] + 1, 'ID':localID}})
                    
                    if( (str(key) not in data) and (clientCmKey == str(key)) ):
                        await contactSingleInstance(lastAddrContacted, clientCmKey)
                        data.update({str(key):{'value':incomingValue, 'version':incomingVersion + 1, 'ID':localID}})

                    if( (str(key) not in data) and (clientCmKey != str(key)) ):
                        await contactSingleInstance(lastAddrContacted, clientCmKey)
                        data.update({str(key):{'value':incomingValue, 'version':1, 'ID':localID}})

                    localKeyData = data[str(key)]
                    localValue   = localKeyData['value']
                    localVersion = localKeyData['version']

                    updateDict.update({'key':str(key), 'value':localValue, 'version':localVersion})
                    
                    await updateOtherInstances(updateDict)
                
                elif(str(key) in data):
                    localKeyData = data[str(key)]
                    localVersion = localKeyData['version']
                    data.update({str(key):{'value':incomingValue, 'version':localVersion + 1}})

                elif(str(key) not in data):
                    data.update({str(key):{'value':incomingValue, 'version':1}})
            
                vectorClock.updateVCDelivery(incomingVC)

                localVC           = vectorClock.returnVC()
                localKeyData      = data[str(key)]
                localVersion      = localKeyData['version']

                return response.json({"message":"Added successfully", "causal-metadata": {'vectorclock':localVC, 'key':key, 'version':localVersion, 'last_addr_contacted':localAddress}}, status=200)
                
    async def get(self, request, key):

        pass

        

        #{"message":"Retrieved successfully", "causal-metadata": "<V2>", "value": 2}

        

            #return response.json({"message": "Key does not exist.  Check validity of key or try again later."}, status=200)
 

            #return response.json({"message":"Retrieved successfully", "causal-metadata": vc, "value": value}, status=200)

    async def delete(self, request, key):

        localVC = vectorClock.returnVC()
        localAddress = str(os.environ['SOCKET_ADDRESS'])
        localID      = identifierNumDict[localAddress]

        return response.json({"store":data, "causal-metadata":localVC, 'local_address':localAddress, 'localID':localID })

    

        


app.add_route(dataDisperse.as_view(), '/dataStoreDispersal')
app.add_route(viewOps.as_view(), '/key-value-store-view')
app.add_route(dataOps.as_view(), '/key-value-store/<key>')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8085)










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