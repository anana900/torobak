#!/usr/bin/env python3

import RPi.GPIO as GPIO
from multiprocessing import Process, Pipe
import multiprocessing as mp
import logging
import time
import os

PORT_SENSOR_BREAK = 13	# BOARD pin 33, BCM pin 13

def prepare_ports():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(PORT_SENSOR_BREAK, GPIO.IN)

def clean_ports():
	GPIO.cleanup()

def dummy_fun(pipe_conn):
	counter = 0
	while True:
		if GPIO.input(PORT_SENSOR_BREAK) == 0:
			print("proces")
			break
		counter += 1
		if not counter % 13:
			pipe_conn[0].send(counter)
		time.sleep(0.2)

def proces_start(fun, arg=''):
	p = Process(target=fun, args=(arg))
	return p

def main():
	prepare_ports()

	try:
		pipe1 = Pipe()
		p = proces_start(dummy_fun, (pipe1,))
		p.start()
		while True:
			if p.is_alive():
				print("proces zyje")
			if GPIO.input(PORT_SENSOR_BREAK) == 0:
				print("main")
				#break
			print("Odebrane: {}".format(pipe1[1].recv()))
			print("MAIN")
			time.sleep(0.1)
	finally:
		clean_ports()

if __name__ == "__main__":
	main()
