#!/usr/bin/env python3

import time
import os

import logger as lg
logger = lg.mylogger(__name__)

class StepperMotor:
    '''
    Reprezentacja silnika krokowego
    '''
    def __init__(self, \
                 port_dir, \
                 port_step, \
                 motor_deg_step):
        self.port_dir = port_dir
        self.port_step = port_step
        self.motor_deg_step = motor_deg_step

class StepperMotorSensor:
    '''
    Reprezentacja czujników krańcowych
    '''
    def __init__(self, \
                 sms_a, \
                 sms_b = None):
        self.sms_a = sms_a
        self.sms_b = sms_b

class StepperMotorControl:
    '''
    Metody kontroli silnika
    - przyspienienie
    - alarmy czujnikow
    '''
    def __init__(self, \
                 sm, \
                 gpio, \
                 sm_sensor = None, \
                 sm_event_on_sensor = None, \
                 acc_time_low = 0.006, \
                 acc_time_high = 0.002, \
                 acc_time_resol = 0.0002):
        self.sm = sm
        self.gpio = gpio
        self.sm_sensor = sm_sensor
        self.sm_event_on_sensor = sm_event_on_sensor
        self.acc_time_low = acc_time_low
        self.acc_time_high = acc_time_high
        self.acc_time_resol = acc_time_resol
        self.acc_time_current = self.acc_time_low

    def _smc_set_direction(self, direction):
        self.gpio.output(self.sm.port_dir, direction)

    def _smc_set_step(self, wait):
        self.gpio.output(self.sm.port_step, self.gpio.HIGH)
        time.sleep(wait)
        self.gpio.output(self.sm.port_step, self.gpio.LOW)
        time.sleep(wait)

    def _get_sm_ramp_up(self):
        return int((self.acc_time_low - self.acc_time_high) / self.acc_time_resol)

    def _smc_accelerate(self, acc_type, no_of_steps):
        while no_of_steps:
            logger.debug("proc {} -sm-> {}".format(os.getpid(), self.acc_time_current))
            self._smc_set_step(self.acc_time_current)
            if acc_type == 1:
                self.acc_time_current -= self.acc_time_resol
            elif acc_type == -1:
                self.acc_time_current += self.acc_time_resol
            elif acc_type == 0:
                pass
            self.acc_time_current = round(self.acc_time_current, 5)
            no_of_steps -= 1

    def smc_move(self, direction, no_of_steps):
        self._smc_set_direction(direction)

        self.add_odd_step = 0
        if no_of_steps % 2:
            self.add_odd_step = 1

        self.no_of_steps_half = no_of_steps // 2

        if self.no_of_steps_half >= 0:
            if self._get_sm_ramp_up() <= self.no_of_steps_half:
                logger.debug("Stepper acc fast")
                self._smc_accelerate(1, self._get_sm_ramp_up())
                self._smc_accelerate(0, no_of_steps - self._get_sm_ramp_up() * 2)
                self._smc_accelerate(-1, self._get_sm_ramp_up())

            elif self._get_sm_ramp_up() > self.no_of_steps_half:
                logger.debug("Stepper acc slow")
                self._smc_accelerate(1, self.no_of_steps_half)
                self._smc_accelerate(-1, self.no_of_steps_half + self.add_odd_step)

            self.acc_time_current = self.acc_time_low

        else:
            logger.error("Incorrect data")
