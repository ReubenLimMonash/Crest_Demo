"""
Date: 28/09/2023
Desc: GCS Application - Listens for incoming UDP packets from UAV and sends CNC to UAV
        Simple Python socket server & client.
Modified: 01/04/2024
          To include MQTT comm. of throughput data
"""

import socket
import os, time
import argparse
import threading
import json
import logging
import random

from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import MQTTProtocolVersion

# Application Parameters
GCS_IP = '127.0.0.1'
GCS_PORT = 5005
UAV_IP = '127.0.0.1'
UAV_PORT = 5006
VIDEO_PORT = 8080
NUM_PKT = 100 # Number of packets to send
SEND_INT = 20 # GCS sending interval in ms
PKT_SIZE = 100 # GCS Packet Size in bytes
START_TIME = 0
CSV_PATH = "C:/Users/Reuben/OneDrive - Monash University/Documents/PhDLocal/Experiment/"
CSV_NAME = "Test"

# MQTT Parameters
BROKER = 'localhost'
PORT = 1883
CLIENT_ID = f'python-mqtt-tcp-pub-sub-{random.randint(0, 1000)}' # generate client ID with pub prefix randomly
FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

class Mqtt_Pub:
    def __init__(self, broker_ip, broker_port, client_id, topic, reconnect_rate, first_reconnect_delay, max_reconnect_count, max_reconnect_delay):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.client_id = client_id
        self.topic = topic
        self.reconnect_rate = reconnect_rate
        self.first_reconnect_delay = first_reconnect_delay
        self.max_reconnect_count = max_reconnect_count
        self.max_reconnect_delay = max_reconnect_delay
        self.flag_exit = False
        self.connect_mqtt()
        self.client.loop_start()
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0 and self.client.is_connected():
            print("Connected to MQTT Broker!")
        else:
            print(f'Failed to connect, return code {rc}')


    def on_disconnect(self, client, userdata, rc):
        logging.info("Disconnected with result code: %s", rc)
        reconnect_count, reconnect_delay = 0, self.first_reconnect_delay
        while reconnect_count < self.max_reconnect_count:
            logging.info("Reconnecting in %d seconds...", reconnect_delay)
            time.sleep(reconnect_delay)

            try:
                self.client.reconnect()
                logging.info("Reconnected successfully!")
                return
            except Exception as err:
                logging.error("%s. Reconnect failed. Retrying...", err)

            reconnect_delay *= self.reconnect_rate
            reconnect_delay = min(reconnect_delay, self.max_reconnect_delay)
            reconnect_count += 1
        logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)
        self.flag_exit = True

    def on_message(self, client, userdata, msg):
        print(f'Received `{msg.payload.decode()}` from `{msg.topic}` topic')

    def connect_mqtt(self):
        self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1,
                                    self.client_id,
                                    clean_session=True,
                                    userdata=None,protocol=MQTTProtocolVersion.MQTTv311,
                                    transport="tcp")
        # client.username_pw_set(USERNAME, PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_ip, self.broker_port, keepalive=120)
        self.client.on_disconnect = self.on_disconnect
        return self.client

    def publish(self, message):
        if not self.flag_exit:
            msg_dict = {
                'msg': message
            }
            msg = json.dumps(msg_dict)
            if not self.client.is_connected():
                logging.error("publish: MQTT client is not connected!")
                return
            result = self.client.publish(self.topic, msg)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f'Send `{msg}` to topic `{self.topic}`')
            else:
                print(f'Failed to send message to topic {self.topic}')
        return

    def stop(self):
        self.client.loop_stop()
            
def parseArg():
    global GCS_IP
    global GCS_PORT
    global UAV_IP
    global UAV_PORT
    global VIDEO_PORT
    global CSV_PATH
    global CSV_NAME
    global NUM_PKT
    global SEND_INT
    global PKT_SIZE
    parser = argparse.ArgumentParser(description='''Usage: python gcs_app.py --gcs_ip 127.0.0.1 --gcs_port 5005 --uav_ip 127.0.0.1 --uav_port 5006 --video_port 8080
                                    --csv_path "C:/Users/Reuben/OneDrive - Monash University/Documents/PhDLocal/Experiment" --csv_name Test 
                                    --num_pkt 100 --send_int 20 --pkt_size 100''')
    parser.add_argument('--gcs_ip', type=str, help='IP Address of GCS')
    parser.add_argument('--gcs_port', type=int, help='Listening port of GCS Server')
    parser.add_argument('--uav_ip', type=str, help='IP Address of UAV')
    parser.add_argument('--uav_port', type=int, help='Listening port of UAV Server')
    parser.add_argument('--video_port', type=int, help='Listening port of GCS Video Server')
    parser.add_argument('--csv_path', type=str, help='Path to save CSV results')
    parser.add_argument('--csv_name', type=str, help='Path to save CSV results')
    parser.add_argument('--num_pkt', type=int, help='Number of packets to send')
    parser.add_argument('--send_int', type=int, help='GCS sending interval in ms')
    parser.add_argument('--pkt_size', type=int, help='GCS Packet Size in bytes')
    args = parser.parse_args()
    if args.gcs_ip is not None:
        GCS_IP = args.gcs_ip
    if args.gcs_port is not None:
        GCS_PORT = args.gcs_port
    if args.uav_ip is not None:
        UAV_IP = args.uav_ip
    if args.uav_port is not None:
        UAV_PORT = args.uav_port
    if args.video_port is not None:
        VIDEO_PORT = args.video_port
    if args.csv_path is not None:
        CSV_PATH = args.csv_path
    if args.csv_name is not None:
        CSV_NAME = args.csv_name
    if args.num_pkt is not None:
        NUM_PKT = args.num_pkt
    if args.send_int is not None:
        SEND_INT = args.send_int
    if args.pkt_size is not None:
        PKT_SIZE = args.pkt_size
    return 

def gcs_server_app(server, csv_file, mqtt_client=None):
    '''
    server: server socket
    csv_file: CSV File Name to record packets
    '''
    with open(csv_file, 'w+', buffering=1) as f:
        print("####### GCS Server is listening #######")
        print("StartTime, {}".format(time.time()), file=f)
        print("Seq, RxTime, Length, Address", file=f)
        while True:
            try:
                data, address = server.recvfrom(4096)
                seq = data.decode('utf-8').split('u')[0]
                print("{}, {}, {}, {}".format(seq, time.time(), len(data), address[0]), file=f)
                if mqtt_client is not None:
                    mqtt_client.publish(len(data)) # Publish the message length
            except KeyboardInterrupt:
                if server:
                    server.close()
                break

def gcs_video_server_app(video_server, csv_file):
    '''
    server: server socket
    csv_file: CSV File Name to record packets
    '''
    with open(csv_file, 'w+', buffering=1) as f:
        print("####### GCS Video is listening #######")
        print("StartTime, {}".format(time.time()), file=f)
        print("Seq, RxTime, Length, Address", file=f)
        while True:
            try:
                data, address = video_server.recvfrom(4096)
                seq = data.decode('utf-8').split('v')[0]
                print("{}, {}, {}, {}".format(seq, time.time(), len(data), address[0]), file=f)
            except KeyboardInterrupt:
                if video_server:
                    video_server.close()
                break

def gcs_send_app(send_soc, uav_ip, uav_port, send_int, pkt_size, csv_file):
    '''
    send_soc: sending socket
    send_int: Sending Interval
    csv_file: CSV File Name to record packets
    '''
    with open(csv_file, 'w+', buffering=1) as f:
        print("####### GCS Sender is sending #######")
        print("StartTime, {}".format(time.time()), file=f)
        print("Seq, TxTime, Length, Address", file=f)
        try:
            for i in range(NUM_PKT):
                send_time = time.time()
                send_data = str(i) + 'g' * (pkt_size-len(str(i)))
                send_soc.sendto(send_data.encode('utf-8'), (uav_ip, uav_port))
                print("{}, {}, {}, {}".format(i, send_time, len(send_data), uav_ip), file=f)
                curr_time = time.time()
                while (curr_time - send_time) < send_int/1000:
                    curr_time = time.time()
            print("####### GCS Sender Done #######")
        except KeyboardInterrupt:
            if send_soc:
                send_soc.close()
        
if __name__ == "__main__":
    parseArg()
    # Create a UDP socket
    gcs_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gcs_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gcs_video_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the server socket to the port
    gcs_server_address = (GCS_IP, GCS_PORT)
    gcs_video_server_address = (GCS_IP, VIDEO_PORT)
    gcs_server.bind(gcs_server_address)
    gcs_video_server.bind(gcs_video_server_address)

    # Create MQTT Publisher
    mqtt_pub_gcs = Mqtt_Pub(BROKER, PORT, CLIENT_ID, "gcs_recv", RECONNECT_RATE, FIRST_RECONNECT_DELAY, MAX_RECONNECT_COUNT, MAX_RECONNECT_DELAY)

    # Start GCS Server
    server_th = threading.Thread(target=gcs_server_app, args=(gcs_server, os.path.join(CSV_PATH, CSV_NAME + "_GCS-Sink.csv"), mqtt_pub_gcs))
    server_th.daemon = True
    server_th.start()
    # Start GCS Video Server
    # video_server_th = threading.Thread(target=gcs_video_server_app, args=(gcs_video_server, os.path.join(CSV_PATH, CSV_NAME + "_GCS-VideoSink.csv")))
    # video_server_th.daemon = True
    # video_server_th.start()
    # Start GCS Client Sender
    time.sleep(5) # Let's wait 5 seconds before starting the sender
    sender_th = threading.Thread(target=gcs_send_app, args=(gcs_sender, UAV_IP, UAV_PORT, SEND_INT, PKT_SIZE, os.path.join(CSV_PATH, CSV_NAME + "_GCS-Source.csv")))
    sender_th.daemon = True
    sender_th.start()

    sender_th.join()
    server_th.join()
    # video_server_th.join()
    