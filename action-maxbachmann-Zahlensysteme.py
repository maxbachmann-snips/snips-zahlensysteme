#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import io
import paho.mqtt.client as mqtt
import random
import json

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

class SnipsConfigParser(configparser.SafeConfigParser):
    def to_dict(self):
        return {section: {option_name: option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, configparser.Error) as e:
        return dict()

conf = read_configuration_file(CONFIG_INI)
print("Conf:", conf)

# MQTT client to connect to the bus
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    client.subscribe("hermes/intent/#")

def message(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    try:
        slots = {slot['slotName']: slot['value']['value'] for slot in data['slots']}

        answer = '<speak>' + int(slots['value']) + ' ist als ' + slots['type'] + 'zahl '
        value_new = ''

        if slots['type'] == 'binär':
            value_new = bin(int(slots['value']))
        elif slots['type'] == 'oktal':
            value_new = oct(int(slots['value']))
        elif slots['type'] == 'hexadezimal':
            value_new = hex(int(slots['value']))
        
        for buchstabe in value_new[:-1]:
            answer += buchstabe + ' <break time="300ms"/> '
        answer += value_new[-1] + '</speak>'
        say(session_id, answer)
    except KeyError:
        pass

def say(session_id, text):
    mqtt_client.publish('hermes/dialogueManager/endSession',
                        json.dumps({'text': text, "sessionId": session_id}))

if __name__ == "__main__":
    mqtt_client.on_connect = on_connect
    mqtt_client.message_callback_add("hermes/intent/maxbachmann:zahlensysteme/#", message)
    mqtt_client.connect("localhost", 1883)
    mqtt_client.loop_forever()
