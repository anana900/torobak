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
                 acc_time_high = 0.002):
        self.sm = sm
        self.gpio = gpio
        self.sm_sensor = sm_sensor
        self.sm_event_on_sensor = sm_event_on_sensor
        self.acc_time_low = acc_time_low
        self.acc_time_high = acc_time_high
        self.acc_time_current = self.acc_time_low

    def _smc_set_direction(self, direction):
        self.gpio.output(self.sm.port_dir, direction)

    def _smc_set_step(self, wait):
        self.gpio.output(self.sm.port_step, self.gpio.HIGH)
        time.sleep(wait)
        self.gpio.output(self.sm.port_step, self.gpio.LOW)
        time.sleep(wait)

    def smc_ramp_up(self, nr_kroku, opoznienie):
        '''
        Opracowane na podstawie http://ww1.microchip.com/downloads/en/AppNotes/doc8017.pdf
        '''
        nastepne_opoznienie = opoznienie - (2 * opoznienie / (4 * nr_kroku + 1))
        return nastepne_opoznienie

    def smc_ramp_down(self, nr_kroku, opoznienie):
        '''
        Opracowane na podstawie http://ww1.microchip.com/downloads/en/AppNotes/doc8017.pdf
        '''
        nastepne_opoznienie = (opoznienie * (4 * nr_kroku + 1)) / (4 * nr_kroku - 1)
        return nastepne_opoznienie

    def smc_read_sensor(self, sm_sensor_no):
        if self.gpio.input(sm_sensor_no) == self.gpio.HIGH:
            logging.info("Reached End")
            return True
        return False

    def smc_move(self, kierunek, ilosc_krokow_do_wykonania):
        '''
        Ustawienie kierunku i wykonanie zadanej liczby kroków
        Funkcja wykożystuje 2 medoty:
        - smc_ramp_up - oblicza opoznienie czasowe dla przyspieszenia
        - smc_ramp_down - oblicza opoznienie czasowe dla zwolnienia
        '''
        # ustaw kierunek obrotow silnika
        self._smc_set_direction(kierunek)

        polowa_krokow = ilosc_krokow_do_wykonania // 2
        nr_kroku = 0

        if ilosc_krokow_do_wykonania > 0:
            flaga_czy_przyspieszamy = 1
            opoznienie = 0

            # glowna petla - iterowanie po zadanej liczbie krokow do wykonania
            for krok in range(ilosc_krokow_do_wykonania):
                
                # ustawienie flagi decydujacej o przyspieszeniu lub zwolnieniu
                if krok > polowa_krokow:
                    flaga_czy_przyspieszamy = 0

                # oblicznie opoznienia dla przyspiezsenia
                if flaga_czy_przyspieszamy == 1:
                    nr_kroku += 1
                    opoznienie = self.smc_ramp_up(nr_kroku, opoznienie)  
                # obliczanie opoznienia czasowego dla zwolnienia
                elif flaga_czy_przyspieszamy == 0:
                    nr_kroku -= 1
                    opoznienie = self.smc_ramp_down(nr_kroku, opoznienie)

                # wykonanie pierwszego kroku z najnizsza zdefiniowana predkoscia
                if krok == 0:
                    opoznienie = self.acc_time_low

                # sprawdz czy opoznienie jest najmniejsze (najwieksza predkosc)
                if opoznienie <= self.acc_time_high:
                    logger.debug("step {}, counter {}, delay {}".format(krok, nr_kroku, self.acc_time_high))
                    self._smc_set_step(self.acc_time_high)
                else:
                    logger.debug("step {}, counter {}, delay {}".format(krok, nr_kroku, round(opoznienie,7)))
                    self._smc_set_step(round(opoznienie,7))

        elif ilosc_krokow_do_wykonania < 0:
            logger.error("Number of steps must be higher than 0, not {}".format(ilosc_krokow_do_wykonania))
