# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

import argparse
import uuid
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
from uuid import uuid4
import json

# This sample uses the Message Broker for AWS IoT to send and receive messages
# through an MQTT connection. On startup, the device connects to the server,
# subscribes to a topic, and begins publishing messages to that topic.
# The device should receive those same messages back from the message broker,
# since it is subscribed to that same topic.
client_id = "rapsberry-001"
cafile="/home/pi/certs/AmazonRootCA1.pem"
cert = "/home/pi/certs/7042485e20-certificate.pem.crt"
pkey = "/home/pi/certs/7042485e20-private.pem.key"
endpoint = "a3d2a52ezvc95n-ats.iot.us-east-1.amazonaws.com"
topic = "tcu-pi/pi123"

io.init_logging(0, 'stderr')

received_count = 0
received_all_event = threading.Event()

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        print("Resubscribe results: {}".format(resubscribe_results))

        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))



if __name__ == '__main__':
    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)



    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        port=8883,
        cert_filepath=cert,
        pri_key_filepath=pkey,
        client_bootstrap=client_bootstrap,
        ca_filepath=cafile,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=client_id,
        clean_session=False,
        keep_alive_secs=30)

    print("Connecting to {} with client ID '{}'...".format(
        endpoint, client_id))

    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    trip_id = uuid.uuid4()

    message = {
     "name": "speed",
     "value": 87,
     "vin": "123445656677777",
     "trip_id": trip_id  

    }
    message = json.json_encode(message)
    # Publish message to server desired number of times.
    # This step is skipped if message is blank.
    # This step loops forever if count was set to 0.

    publish_count = 1
    while (publish_count <= 10) :
        message = "{} [{}]".format(args.message, publish_count)
        print("Publishing message to topic '{}': {}".format(topic, message))
        mqtt_connection.publish(
            topic=topic,
            payload=message,
            qos=mqtt.QoS.AT_LEAST_ONCE)
        time.sleep(1)
        publish_count += 1

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")
