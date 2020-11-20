#!/bin/bash

sudo docker run -p 8084:8085 --net=mynet --ip=10.10.0.4 --name="replica3" -e SOCKET_ADDRESS="10.10.0.4:8085" -e VCVALUES="0,0,0" -e VIEW="10.10.0.2:8085,10.10.0.3:8085,10.10.0.4:8085" server python3 asgn3_4.py

