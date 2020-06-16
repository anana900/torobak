#!/usr/bin/env python3

import importlib
import time
import os
import sys
from multiprocessing import Process
import multiprocessing as mp

import logger as lg
from threading import ThreadError
logger = lg.mylogger(__name__)

PLATFORM_SPECIFIC_MODULES = ["RPi.GPIO", "stepper_motor"]

for module_item in PLATFORM_SPECIFIC_MODULES:
    if not importlib.util.find_spec(module_item):
        logger.error("Module {} does not exist".format(module_item))
        exit(1)

import RPi.GPIO as GPIO
import stepper_motor as sm

smz_dir = 18					# BOARD pin 12, BCM pin 18
smz_step = 27					# BOARD pin 13, BCM pin 27
smz_sensor_end_top = 18			# BOARD pin 12, BCM pin 18
smz_sensor_end_bot = 27			# BOARD pin 13, BCM pin 27

def prepare_ports():
    logger.debug("Setting device ports")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(smz_dir, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(smz_step, GPIO.OUT, initial=GPIO.LOW)

def clean_ports():
    logger.debug("Cleaning device ports")
    GPIO.cleanup()

def main(argv):
    prepare_ports()
    try:
        stepper_motor_z = sm.StepperMotor(smz_dir, smz_step, 2)
        stepper_motor_z_sensor = sm.StepperMotorSensor(smz_sensor_end_top, smz_sensor_end_bot)
        
        stepper_motor_control_z = sm.StepperMotorControl(stepper_motor_z,\
								GPIO,\
								stepper_motor_z_sensor,\
								None,\
								0.0052,\
								0.0002,\
								0.0001)
        #stepper_motor_control_z.smc_move(int(sys.argv[1]), int(sys.argv[2]))
        p1 = mp.Process(target=stepper_motor_control_z.smc_move, args=(int(sys.argv[1]), int(sys.argv[2])))
        p1.start()
        p1.join()
    finally:
        clean_ports()

if __name__ == '__main__':
	main(sys.argv)
