#!/usr/bin/env python
# -*- coding: utf-8 -*-
from messaging.sms import SmsSubmit, SmsDeliver
import serial
import time
import csv
import re
from datetime import datetime


__author__ = "Mathias Schuepany (https://github.com/schue30/)"
__copyright__ = "Copyright (C) 2015 Mathias Schuepany (https://github.com/schue30/)"
__license__ = "MIT License"
__version__ = "1.0"


# default variables
defaultTTY = "/dev/ttyUSB0"
secondTTY = "/dev/ttyUSB2"
baudrate = 115200
ussd_balance = "*102#"
ussd_loadcard = "*104*"


def send_sms(number, text):
    pdu = SmsSubmit(number, text.decode('utf-8')).to_pdu()
    for pdu in pdu:
        ser.write('AT+CMGS=%d\r' % pdu.length)
        while True:
            char = ser.read(1)
            if len(char) > 0 and '>' in char:
                break
        ser.write('%s\x1a' % pdu.pdu)
        result = ""
        msgid = ""
        msgstatus = ""
        while True:
            char = ser.read(1)
            if len(char) > 0:
                result = result + char
            if re.match("^[ ]*[\r\n]*\+CMGS: [0-9]*[\r\n]+$", result):  # get msg id - (0-255)
                msgid = result.strip()[6:].strip()
                result = ""  # reset
                print " " + str(msgid) + " - ",
            if msgid is not "" and re.match('^[\r\n]*[ -~]+[\r\n]+$', result):  # get status - (default) OK
                msgstatus = result.strip()
                print msgstatus
                break


def send_ussd(ussd):
    serMain = serial.Serial(defaultTTY, baudrate, timeout=1)
    serResult = serial.Serial(secondTTY, baudrate, timeout=1)
    time.sleep(1)
    serMain.write('AT+CUSD=1,"%s",15\r' % ussd)
    start = "+CUSD:"
    result = ""
    while True:
        char = serResult.read(1)
        if len(char) > 0:
            result = result + char
        if start in result and "\",15" in result:
            break
    serMain.close()
    serResult.close()
    return result.strip()[10:-4]


def load_card(code):
    return send_ussd(ussd_loadcard + str(code) + "#")


def get_balance():
    return send_ussd(ussd_balance)


def send_single_sms(number, text):
    ser = serial.Serial(defaultTTY, baudrate, timeout=1)
    time.sleep(1)
    ser.write('AT+CMGF=0\r') # set to pdu mode
    send_sms(number, text)
    ser.close()


def send_multiple_sms(file, text):
    ser = serial.Serial(defaultTTY, baudrate, timeout=1)
    time.sleep(1)
    ser.write('AT+CMGF=0\r') # set to pdu mode
    with open(file, 'rb') as csvfile:
        numberreader = csv.reader(csvfile, delimiter=';', quotechar='|')
        i = 1
        for row in numberreader:
            print str(i) + " - " + row[0] + " - " + row[1].decode('latin-1')
            send_sms(row[0], text)
            i = i + 1
            time.sleep(1)
    ser.close()


if __name__ == "__main__":
    text = "test" # message that should be sent
    file = "members.csv" # file for multiple sms recipients (format: +436661234567;Lastname Firstname)
    number = "+436661234567" # number for single sms
	
    send_single_sms(number, text) #send one sms
    send_multiple_sms(file, text) #send multiple sms

    print "\nLoad credit of prepaid card:"
    print load_card("12345678912345")

    print "\nCurrent balance:"
    print get_balance()
