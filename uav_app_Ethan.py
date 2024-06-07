"""
Date: 28/09/2023
Desc: UAV Application - Listens for incoming UDP packets from GCS and sends CNC to GCS
        Simple Python socket server & client.
"""

import socket
import os, time
import argparse
import threading
import json
import logging
import random
from ping3 import ping

from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import MQTTProtocolVersion

GCS_IP = '127.0.0.1'
GCS_PORT = 5005
UAV_IP = '127.0.0.1'
UAV_PORT = 5006
VIDEO_PORT = 8080
NUM_PKT = 100 # Number of packets to send
SEND_INT = 200 # UAV sending interval in ms
PKT_SIZE = 100 # UAV Packet Size in bytes
VIDEO_NUM_PKT = 100 # Number of packets to send (video)
VIDEO_SEND_INT = 20 # UAV sending interval in ms (video)
VIDEO_PKT_SIZE = 100 # UAV Packet Size in bytes (video)
CSV_PATH = "C:/Users/Reuben/OneDrive - Monash University/Documents/PhDLocal/Experiment/"
CSV_NAME = "Test"

# MQTT Parameters
BROKER = '192.168.1.107'
PORT = 1883
CLIENT_ID = f'python-mqtt-tcp-pub-sub-{random.randint(0, 1000)}' # generate client ID with pub prefix randomly
FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

class Mqtt_Pub:
    def __init__(self, broker_ip, broker_port, client_id, name, reconnect_rate, first_reconnect_delay, max_reconnect_count, max_reconnect_delay):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.client_id = client_id
        self.name = name
        self.reconnect_rate = reconnect_rate
        self.first_reconnect_delay = first_reconnect_delay
        self.max_reconnect_count = max_reconnect_count
        self.max_reconnect_delay = max_reconnect_delay
        self.flag_exit = False
        self.connect_mqtt()
        self.client.loop_start()
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0 and self.client.is_connected():
            print("Connected to MQTT Broker at {}!".format(self.broker_ip))
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

    def publish(self, message, topic):
        if not self.flag_exit:
            msg_dict = {
                'msg': message
            }
            msg = json.dumps(msg_dict)
            if not self.client.is_connected():
                logging.error("publish: MQTT client is not connected!")
                return
            full_topic = self.name + "/" + topic
            result = self.client.publish(full_topic, msg)
            # result: [0, 1]
            status = result[0]
            # if status == 0:
            #     print(f'Send `{msg}` to topic `{full_topic}`')
            # else:
            #     print(f'Failed to send message to topic {full_topic}')
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
    global VIDEO_NUM_PKT
    global VIDEO_SEND_INT
    global VIDEO_PKT_SIZE
    global BROKER
    parser = argparse.ArgumentParser(description='''Usage: python uav_app.py --gcs_ip 127.0.0.1 --gcs_port 5005 --uav_ip 127.0.0.1 --uav_port 5006 --video_port 8080
                                    --csv_path "C:/Users/Reuben/OneDrive - Monash University/Documents/PhDLocal/Experiment" --csv_name Test 
                                    --num_pkt 100 --send_int 20 --pkt_size 100 --broker localhost''')
    parser.add_argument('--gcs_ip', type=str, help='IP Address of GCS')
    parser.add_argument('--gcs_port', type=int, help='Listening port of GCS Server')
    parser.add_argument('--uav_ip', type=str, help='IP Address of UAV')
    parser.add_argument('--uav_port', type=int, help='Listening port of UAV Server')
    parser.add_argument('--video_port', type=int, help='Listening port of GCS Video Server')
    parser.add_argument('--csv_path', type=str, help='Path to save CSV results')
    parser.add_argument('--csv_name', type=str, help='Path to save CSV results')
    parser.add_argument('--num_pkt', type=int, help='Number of packets to send')
    parser.add_argument('--send_int', type=int, help='UAV sending interval in ms')
    parser.add_argument('--pkt_size', type=int, help='UAV Packet Size in bytes')
    parser.add_argument('--vid_num_pkt', type=int, help='Number of packets to send')
    parser.add_argument('--vid_send_int', type=int, help='UAV sending interval in ms')
    parser.add_argument('--vid_pkt_size', type=int, help='UAV Packet Size in bytes')
    parser.add_argument('--broker', type=str, help='IP address of the MQTT broker')
    args = parser.parse_args()
    if args.gcs_ip is not None:
        GCS_IP = args.gcs_ip
    if args.gcs_port is not None:
        GCS_PORT = args.gcs_port
    if args.uav_ip is not None:
        UAV_IP = args.uav_ip
    if args.uav_port is not None:
        UAV_PORT = args.uav_port
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
    if args.vid_num_pkt is not None:
        VIDEO_NUM_PKT = args.vid_num_pkt
    if args.vid_send_int is not None:
        VIDEO_SEND_INT = args.vid_send_int
    if args.vid_pkt_size is not None:
        VIDEO_PKT_SIZE = args.vid_pkt_size
    if args.broker is not None:
        BROKER = args.broker
    return 

def uav_server_app(server, csv_file, mqtt_client=None):
    '''
    server: server socket
    csv_file: CSV File Name to record packets
    '''
    with open(csv_file, 'w+', buffering=1) as f:
        print("####### UAV Server is listening #######")
        print("StartTime, {}".format(time.time()), file=f)
        print("Seq, RxTime, Length, Address", file=f)
        while True:
            try:
                data, address = server.recvfrom(4096)
                rxTime = time.time()
                remainder = data.decode('utf-8').split('-')
                seq = remainder[0]
                txTime = remainder[1].split('g')[0]
                # delay = rxTime - float(txTime)
                delay = ping(GCS_IP)
                print("Average rtt: {}".format(delay))
                print("{}, {}, {}, {}".format(seq, rxTime, len(data), address[0]), file=f)
                if mqtt_client is not None:
                    mqtt_client.publish(len(data), 'length') # Publish the message length
                    mqtt_client.publish(delay, 'delay') # Publish the delay in ms
            except KeyboardInterrupt:
                if server:
                    server.close()
                break

def uav_send_app(send_soc, gcs_ip, gcs_port, send_int, pkt_size, csv_file):
    '''
    send_soc: sending socket
    csv_file: CSV File Name to record packets
    '''
    with open(csv_file, 'w+', buffering=1) as f:
        print("####### UAV Sender is sending #######")
        print("StartTime, {}".format(time.time()), file=f)
        print("Seq, TxTime, Length, Address", file=f)
        i = 0
        try:
            # for i in range(NUM_PKT):
            while(True):
                i += 1
                send_time = time.time()
                send_data = str(i) + '-' + str(send_time) + 'u' * (pkt_size-len(str(i)+str(send_time)))
                send_soc.sendto(send_data.encode('utf-8'), (gcs_ip, gcs_port))
                print("{}, {}, {}, {}".format(i, send_time, len(send_data), gcs_ip), file=f)
                curr_time = time.time()
                while (curr_time - send_time) < send_int/1000:
                    curr_time = time.time()
                # print("Sent a message of seq {} at time {}".format(i, send_time))
        except KeyboardInterrupt:
            if send_soc:
                send_soc.close()

def uav_video_send_app(send_soc, gcs_ip, video_port, send_int, pkt_size, csv_file):
    '''
    send_soc: sending socket
    csv_file: CSV File Name to record packets
    '''
    with open(csv_file, 'w+', buffering=1) as f:
        print("####### UAV Video is sending #######")
        print("StartTime, {}".format(time.time()), file=f)
        print("Seq, TxTime, Length, Address", file=f)
        try:
            for i in range(VIDEO_NUM_PKT):
                send_time = time.time()
                send_data = str(i) + 'v' * (pkt_size-len(str(i)))
                send_soc.sendto(send_data.encode('utf-8'), (gcs_ip, video_port))
                print("{}, {}, {}, {}".format(i, send_time, len(send_data), gcs_ip), file=f)
                curr_time = time.time()
                while (curr_time - send_time) < send_int/1000:
                    curr_time = time.time()
            print("####### UAV Video Done #######")
        except KeyboardInterrupt:
            if send_soc:
                send_soc.close()

if __name__ == "__main__":
    parseArg()
    # Create a UDP socket
    uav_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    uav_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    uav_video_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the server socket to the port
    uav_server_address = (UAV_IP, UAV_PORT)
    uav_server.bind(uav_server_address)

    # Create MQTT Publisher
    mqtt_pub_uav = Mqtt_Pub(BROKER, PORT, CLIENT_ID, "uav_recv", RECONNECT_RATE, FIRST_RECONNECT_DELAY, MAX_RECONNECT_COUNT, MAX_RECONNECT_DELAY)

    server_th = threading.Thread(target=uav_server_app, args=(uav_server, os.path.join(CSV_PATH, CSV_NAME + "_UAV-Sink.csv"), mqtt_pub_uav))
    server_th.daemon = True
    server_th.start()
    time.sleep(5) # Let's wait 5 seconds before starting the sender
    sender_th = threading.Thread(target=uav_send_app, args=(uav_sender, GCS_IP, GCS_PORT, SEND_INT, PKT_SIZE, os.path.join(CSV_PATH, CSV_NAME + "_UAV-Source.csv")))
    sender_th.daemon = True
    video_sender_th = threading.Thread(target=uav_video_send_app, args=(uav_sender, GCS_IP, VIDEO_PORT, VIDEO_SEND_INT, VIDEO_PKT_SIZE, os.path.join(CSV_PATH, CSV_NAME + "_UAV-VideoSource.csv")))
    video_sender_th.daemon = True
    sender_th.start()
    video_sender_th.start()

    sender_th.join()
    video_sender_th.join()
    server_th.join()

    
