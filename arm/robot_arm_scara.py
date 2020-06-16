#!/usr/bin/env python3

import RPi.GPIO as GPIO
from multiprocessing import Process
import multiprocessing as mp
import logging
import time
import os

import br_logging as lg
logger = lg.mylogger(__name__)

import br_scara_arm as sa
import br_stepper_motor as sm

#mp.set_start_method('spawn')

sm1_dir = 18	# BOARD pin 12, BCM pin 18
sm1_step = 27	# BOARD pin 13, BCM pin 27
sm2_dir = 22	# BOARD pin 15, BCM pin 22
sm2_step = 23	# BOARD pin 16, BCM pin 23

SM_SCARA_SPR = 200
SM_VERTICAL_SPR = 200

delayMin = 0.0004 # SPEED
delayMax = 0.0004
accSteps = int(delayMax/delayMin)
targetSteps = 150 # step

def prepare_ports():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(sm1_dir, GPIO.OUT, initial=GPIO.LOW)
	GPIO.setup(sm1_step, GPIO.OUT, initial=GPIO.LOW)
	GPIO.setup(sm2_dir, GPIO.OUT, initial=GPIO.LOW)
	GPIO.setup(sm2_step, GPIO.OUT, initial=GPIO.LOW)

def clean_ports():
	GPIO.cleanup()



def sm_single_step(step, wait=delayMin):
	GPIO.output(step, GPIO.HIGH)
	time.sleep(wait)
	GPIO.output(step, GPIO.LOW)
	time.sleep(wait)

def sm_move(motor, dir, steps):
	name = mp.current_process().name
	logger.debug("{} start".format(name))

	delayCurrent = delayMax

	try:
		if not motor.isBusy:
			motor.isBusy = True
			GPIO.output(motor.dir_port, dir)

			for i in range(steps):
				# odbierz sensor - jesli true to break
				# odbierz obraz - jesli true to break
				sm_single_step(motor.step_port, delayCurrent)

			motor.isBusy = False
		else:
			logger.debug("Motor busy")
	except e:
		logger.debug("Motor Error {}".format(e))
	finally:
		logger.debug("{} end".format(name))

class SMMotor:
	def __init__(self, dir_port, step_port, name=""):
		self.name = name
		self.dir_port = dir_port
		self.step_port = step_port
		self.isBusy = False
		logger.info("New SM created: {}".format(name))




def proces_sm(arm, dir, step):
	#logger.debug("arm {} dir {} step {}".format(arm, dir, step))
	p = Process(target=sm_move, args=(arm, dir, step))
	return p

def translate_scara_to_sm(sm_SPR, scara_angles):
	direction1, direction2 = 0, 0
	angle1, angle2 = scara_angles
	single_step = float(360/sm_SPR)

	if angle1 == None:
		angle1 = 0
	if angle2 == None:
		angle2 = 0
	if angle1 < 0:
		direction1 = 1
	if angle2 < 0:
		direction2 = 1

	return (direction1, int(abs(angle1) / single_step), \
		direction2, int(abs(angle2) / single_step))

def scara_calibrate():
	CALIBRATION_DELAY = 0.01

	arm1_sensor_count = 0
	arm2_sensor_count = 0


def main():
	prepare_ports()
	scara = sa.ScaraArm(5, 5)
	ramie1 = SMMotor(sm1_dir, sm1_step, "R1")
	ramie2 = SMMotor(sm2_dir, sm2_step, "R2")

	p1 = proces_sm(ramie1, 0, 0)
	p2 = proces_sm(ramie2, 0, 0)

	try:
		for x,y, in [(10,0),(5,5),(3,-3),(5,5),(4,1),(-1,-5),(0,-7),(8,1),(3,1),(-5,3),(5,5),(5,5),(10,0)]:
			while p1.is_alive() or p2.is_alive():
				time.sleep(0.1)
			smKat = translate_scara_to_sm(SM_SCARA_SPR, scara.calc_scara_angles(x,y))
			p1 = proces_sm(ramie1, smKat[0], smKat[1])
			p2 = proces_sm(ramie2, smKat[2] , smKat[3])
			p1.start()
			p2.start()
			logger.debug("{} {}".format(p1.pid,p2.pid))
			#time.sleep(1)

	finally:
		while p1.is_alive() or p2.is_alive():
			time.sleep(0.1)
		clean_ports()
		pass

if __name__ == "__main__":
	main()
