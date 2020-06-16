#!/usr/bin/env python3

from multiprocessing import Process
import multiprocessing as mp
import logging
import time
import os
import sys
import importlib

import logger as lg
logger = lg.mylogger(__name__)

PLATFORM_SPECIFIC_MODULES = ["RPi.GPIO", "stepper_motor", "scara_calc_simple"]

for module_item in PLATFORM_SPECIFIC_MODULES:
    if not importlib.util.find_spec(module_item):
        logger.error("Module {} does not exist".format(module_item))
        exit(1)

import scara_calc_simple as sa
import stepper_motor as sm
import RPi.GPIO as GPIO

PORT_O_SCARA_ARM1_DIR = 18					# BOARD pin 12
PORT_O_STARA_ARM1_STEP = 27					# BOARD pin 13
PORT_O_SCARA_ARM2_DIR = 22					# BOARD pin 15
PORT_O_SCARA_ARM2_STEP = 23					# BOARD pin 16
PORT_O_Z_ARM_DIR = 24						# BOARD pin 18
PORT_O_Z_ARM_STEP = 10						# BOARD pin 19
PORT_I_SCARA_ARM1_SENSOR_TOP = 9			# BOARD pin 21
PORT_I_SCARA_ARM1_SENSOR_BOTTOM = 25		# BOARD pin 22
PORT_I_SCARA_ARM2_SENSOR_TOP = 11			# BOARD pin 23
PORT_I_SCARA_ARM2_SENSOR_BOTTOM = 8			# BOARD pin 24
PORT_I_Z_ARM_SENSOR_TOP = 7					# BOARD pin 26
PORT_I_Z_ARM_SENSOR_BOTTOM = 5				# BOARD pin 29

def prepare_ports():
    logger.debug("Setting device ports")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PORT_O_SCARA_ARM1_DIR, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PORT_O_STARA_ARM1_STEP, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PORT_O_SCARA_ARM2_DIR, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PORT_O_SCARA_ARM2_STEP, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PORT_O_Z_ARM_DIR, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PORT_O_Z_ARM_STEP, GPIO.OUT, initial=GPIO.LOW)

def clean_ports():
    logger.debug("Cleaning device ports")
    GPIO.cleanup()

def proces_sm(arm, dir, step):
	#logger.debug("arm {} dir {} step {}".format(arm, dir, step))
	p = Process(target=sm_move, args=(arm, dir, step))
	return p

def main():
    prepare_ports()
    try:
        stepper_motor_scara_1 = sm.StepperMotor(PORT_O_SCARA_ARM1_DIR, \
                                                PORT_O_SCARA_ARM1_DIR, 1.8)
        stepper_motor_scara_2 = sm.StepperMotor(PORT_O_SCARA_ARM2_DIR, \
                                                PORT_O_SCARA_ARM2_DIR, 1.8)
        stepper_motor_scara_1_sensor = sm.StepperMotorSensor(PORT_I_SCARA_ARM1_SENSOR_TOP, \
                                                                PORT_I_SCARA_ARM1_SENSOR_BOTTOM)
        stepper_motor_scara_2_sensor = sm.StepperMotorSensor(PORT_I_SCARA_ARM2_SENSOR_TOP, \
                                                                PORT_I_SCARA_ARM2_SENSOR_BOTTOM)
        
        stepper_motor_control_scara_arm1 = sm.StepperMotorControl(stepper_motor_scara_1,\
                                                                GPIO,\
                                                                stepper_motor_scara_1_sensor,\
                                                                None,\
                                                                0.0058,\
                                                                0.0007,\
                                                                0.0002)
        
        stepper_motor_control_scara_arm2 = sm.StepperMotorControl(stepper_motor_scara_2,\
                                                                GPIO,\
                                                                stepper_motor_scara_2_sensor,\
                                                                None,\
                                                                0.0058,\
                                                                0.0007,\
                                                                0.0002)

        #stepper_motor_control_z.smc_move(int(sys.argv[1]), int(sys.argv[2]))
        p1 = mp.Process(target=stepper_motor_control_scara_arm1.smc_move, args=(int(sys.argv[1]), int(sys.argv[2])))
        p2 = mp.Process(target=stepper_motor_control_scara_arm2.smc_move, args=(int(sys.argv[3]), int(sys.argv[4])))
        p1.start()
        p2.start()
        p1.join()
        p2.join()
        
    finally:
        clean_ports()

if __name__ == "__main__":
	main()
