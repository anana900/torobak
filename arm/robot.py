#!/usr/bin/env python3

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
PORT_O_SCARA_ARM1_STEP = 27					# BOARD pin 13
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
    GPIO.setup(PORT_O_SCARA_ARM1_STEP, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PORT_O_SCARA_ARM2_DIR, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PORT_O_SCARA_ARM2_STEP, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PORT_O_Z_ARM_DIR, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PORT_O_Z_ARM_STEP, GPIO.OUT, initial=GPIO.LOW)
    
    GPIO.setup(PORT_I_SCARA_ARM1_SENSOR_TOP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PORT_I_SCARA_ARM2_SENSOR_TOP, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def clean_ports():
    logger.debug("Cleaning device ports")
    GPIO.cleanup()

def main():
    prepare_ports()
    
    wiadomosc = mp.Value('i', 0)
    wiadomosc_lock = mp.Lock()
    
    try:
        # definiowanie ramienia SCARA: R1 20cm, R2 20cm
        scara_arm = sa.ScaraArm(20,20)

        # zdefiniowanie silnikow krokowych dla ramienia SCARA
        stepper_motor_scara_1 = sm.StepperMotor("scara ramie 1", \
                                                PORT_O_SCARA_ARM1_DIR, \
                                                PORT_O_SCARA_ARM1_STEP, 1.8)
        stepper_motor_scara_2 = sm.StepperMotor("scara ramie 2", \
                                                PORT_O_SCARA_ARM2_DIR, \
                                                PORT_O_SCARA_ARM2_STEP, 1.8)
        # zdefiniowanie czujnikow krancowych dla amienie SCARA
        stepper_motor_scara_1_sensor = sm.StepperMotorSensor(PORT_I_SCARA_ARM1_SENSOR_TOP, \
                                                                PORT_I_SCARA_ARM1_SENSOR_BOTTOM)
        stepper_motor_scara_2_sensor = sm.StepperMotorSensor(PORT_I_SCARA_ARM1_SENSOR_TOP, \
                                                                PORT_I_SCARA_ARM2_SENSOR_BOTTOM)

        # stworzenie metod kontrolnych silników poszczególnych ramion
        stepper_motor_control_scara_arm1 = sm.StepperMotorControl(stepper_motor_scara_1,\
                                                                GPIO,\
                                                                stepper_motor_scara_1_sensor,\
                                                                None,\
                                                                0.0016,\
                                                                0.0002) # 0.006, 0.004
        
        stepper_motor_control_scara_arm2 = sm.StepperMotorControl(stepper_motor_scara_2,\
                                                                GPIO,\
                                                                stepper_motor_scara_2_sensor,\
                                                                None,\
                                                                0.0016,\
                                                                0.0002)

        while True:
            print("Number of cpu : ", mp.cpu_count())
            x = input()
            y = input()
            if x == 'x' or y == 'x':
                break

            #dane_r1_r2 = scara_arm.translate_scara_to_sm(3600, scara_arm.calc_scara_angles(int(x),int(y)))
            #p1 = mp.Process(target=stepper_motor_control_scara_arm1.smc_move, args=(dane_r1_r2[0], dane_r1_r2[1], wiadomosc, wiadomosc_lock))
            #p2 = mp.Process(target=stepper_motor_control_scara_arm2.smc_move, args=(dane_r1_r2[2], dane_r1_r2[3], wiadomosc, wiadomosc_lock))

            dane_r1_r2 = scara_arm.translate_scara_to_sm(3600, scara_arm.calc_scara_angles_middle(int(x),int(y)), scara_arm.calc_scara_angles(int(x),int(y)))
            p1 = mp.Process(target=stepper_motor_control_scara_arm1.smc_move_scara, args=(dane_r1_r2[0], dane_r1_r2[1], dane_r1_r2[2], dane_r1_r2[3], wiadomosc, wiadomosc_lock))
            p2 = mp.Process(target=stepper_motor_control_scara_arm2.smc_move_scara, args=(dane_r1_r2[4], dane_r1_r2[5], dane_r1_r2[6], dane_r1_r2[7], wiadomosc, wiadomosc_lock))

            p1.start()
            p2.start()
            p1.join()
            p2.join()

    finally:
        clean_ports()

if __name__ == "__main__":
	main()
