#!/bin/bash


docker stop $(docker ps -a -q)

sudo docker rm $(docker ps -qa)


