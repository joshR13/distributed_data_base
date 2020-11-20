#!/bin/bash


echo "Here is the results from the PUT requests:"

#curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value": 17, "causal-metadata": {"vectorclock":{"10.10.0.2:8085":1, "10.10.0.3:8085":2, "10.10.0.4:8085":3}, "key":"x", "version":1, "last_addr_contacted":"10.10.0.2:8085"}}' http://localhost:8082/key-value-store/y &

curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value": 17, "causal-metadata": ""}' http://localhost:8082/key-value-store/y &

#{'vectorclock':VC, 'key':key, 'version':version, 'last_addr_contacted':localAddress}

curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value": 127, "causal-metadata": ""}' http://localhost:8083/key-value-store/y &


curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value": 27, "causal-metadata": ""}' http://localhost:8084/key-value-store/y &


#curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value": 122, "causal-metadata": ""}' http://localhost:8084/key-value-store/y &

#curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value": 122, "causal-metadata": {"key":x, "value":122, "vcvalue":1}}' http://localhost:8082/key-value-store/x


#echo "$curlResult"

#declare -A associative=$curlResult

#echo $associative

#grep vcvalue $associative 

#echo "Here are the results from GET request"


#curl -v localhost:8083/key-value-store/x #should return the data store

#curl --request DELETE --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8083/key-value-store/y #should return vector clock contents for replica that was contacted

#echo "Here are the results from the veiw GET request to 8082:"

#curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8082/key-value-store-view


#echo "Here are the results from the view GET request to 8084:"

#curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8084/key-value-store-view

