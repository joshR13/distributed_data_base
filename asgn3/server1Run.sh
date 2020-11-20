#!/bin/bash


sudo docker run -p 8082:8085 --net=mynet --ip=10.10.0.2 --name="replica1" -e SOCKET_ADDRESS="10.10.0.2:8085" -e VIEW="10.10.0.2:8085,10.10.0.3:8085,10.10.0.4:8085" -e VCVALUES="2,3,4" server  
 
#i'vectorclock':VC, 'key':key, 'version':version, 'last_addr_contacted':localAddress}
