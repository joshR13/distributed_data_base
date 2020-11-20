#!/bin/bash


sudo docker run -p 8083:8085 --net=mynet --ip=10.10.0.3 --name="replica2" -e SOCKET_ADDRESS="10.10.0.3:8085" -e VIEW="10.10.0.2:8085,10.10.0.3:8085,10.10.0.4:8085" -e VCVALUES="0,0,0" server python3 asgn3_4.py

