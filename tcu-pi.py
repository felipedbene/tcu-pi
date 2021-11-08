from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import time
import uuid
import random
import datetime

#you can use http://randomvin.com/ to generate a VIN number
VIN = "1HGCP2F31BA126162"

#Setup our MQTT client and security certificates
#Make sure your certificate names match what you downloaded from AWS IoT

mqttc = AWSIoTMQTTClient(VIN)

#Make sure you use the correct region!
mqttc.configureEndpoint("data.iot.us-east-1.amazonaws.com",8883)
mqttc.configureCredentials("./root-CA.crt","./tcu-pi.private.key","./tcu-pi.cert.pem")

#Function to encode a payload into JSON
def json_encode(string):
    return json.dumps(string)

mqttc.json_encode=json_encode

#Declaring trip_id variables
trip_id = str(uuid.uuid4())


#This sends our test message to the iot topic
def send():
     message = {
     "name": "speed",
     "value": 87,
     "vin": VIN,
     "trip_id": trip_id
  }

     #Encoding into JSON
     message = mqttc.json_encode(message)

     mqttc.publish("tcu-pi/"+VIN, message, 0)
     print "Message Published" + message

#Connect to the gateway
mqttc.connect()
print "Connected"

#Loop until terminated
while True:
    send()
    time.sleep(1)

mqttc.disconnect()
#To check and see if your message was published to the message broker go to the MQTT Client and subscribe to the iot topic and you should see your JSON Payload
