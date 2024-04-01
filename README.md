# CREST Demo - Dashboard for UAV Throughput

## Setup Node-Red
Install Node-Red for RPi
```
sudo apt install build-essential git curl
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
```
Install Dashboard and Msg-Speed nodes in Node-Red
```
cd ~/.node-red
npm install node-red-dashboard
npm install node-red-contrib-msg-speed
```
Start Node-Red in RPi
```
node-red-pi --max-old-space-size=256
```
## Setup MQTT Broker
Install and start Mosquitto MQTT
```
sudo apt-get install mosquitto mosquitto-clients -y
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```
Install MQTT for Python
```
pip3 install paho-mqtt
```
## Setup Dashboard
1. In a browser, navigate to localhost:1880 to open Node-Red.
2. Import the flows.json file via the toolbar.
3. Open Dashboard view via drop down menu.
## Run GCS and UAV Scripts
Edit the parameters in gcs_app.py and uav_app.py and run them:
```
python3 -m gcs_app
python3 -mm uav_app
```
Alternatively, run with parameters:
```
python gcs_app.py --gcs_ip 127.0.0.1 --gcs_port 5005 --uav_ip 127.0.0.1 --uav_port 5006 --video_port 8080 --csv_path "/home/raspberry/" --csv_name Test
python uav_app.py --gcs_ip 127.0.0.1 --gcs_port 5005 --uav_ip 127.0.0.1 --uav_port 5006 --video_port 8080 --csv_path "/home/raspberry/" --csv_name Test
```
