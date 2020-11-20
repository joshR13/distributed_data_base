#!/bin/bash


echo "Here are the results from the DELETE requests:"


curl --request DELETE --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value": 122, "causal-metadata": ""}' http://localhost:8082/key-value-store/y &

curl --request DELETE --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value": 122, "causal-metadata": ""}' http://localhost:8083/key-value-store/y &

curl --request DELETE --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value": 122, "causal-metadata": ""}' http://localhost:8084/key-value-store/y &


