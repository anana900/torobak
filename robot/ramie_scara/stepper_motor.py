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
                 motor_name, \
                 port_dir, \
                 port_step, \
                 motor_deg_step):
        self.name = motor_name
        self.port_dir = port_dir
        self.port_step = port_step
        self.deg_step = motor_deg_step

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

    def _smc_ramp_up(self, nr_kroku, opoznienie):
        '''
        Opracowane na podstawie http://ww1.microchip.com/downloads/en/AppNotes/doc8017.pdf
        '''
        nastepne_opoznienie = opoznienie - (2 * opoznienie / (4 * nr_kroku + 1))
        return nastepne_opoznienie

    def _smc_ramp_down(self, nr_kroku, opoznienie):
        '''
        Opracowane na podstawie http://ww1.microchip.com/downloads/en/AppNotes/doc8017.pdf
        '''
        nastepne_opoznienie = (opoznienie * (4 * nr_kroku + 1)) / (4 * nr_kroku - 1)
        return nastepne_opoznienie

    def smc_read_sensor(self, sm_sensor_no):
        if self.gpio.input(sm_sensor_no.sms_a) == self.gpio.LOW:
            logger.debug("{} Reached End".format(self.sm.name))
            return True
        return False

    def smc_move(self, kierunek, ilosc_krokow_do_wykonania, wiadomosc, wiadomosc_lock):
        '''
        Ustawienie kierunku i wykonanie zadanej liczby kroków
        Funkcja wykożystuje 2 medoty:
        - _smc_ramp_up - oblicza opoznienie czasowe dla przyspieszenia
        - _smc_ramp_down - oblicza opoznienie czasowe dla zwolnienia
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

                # czytaj wiadomosc, jesli inny silnik zatrzymal prace tez przerwij
                if wiadomosc != 0:
                    if wiadomosc == -1:
                        logger.debug("{} Odbierz wiadomosc, czujnik krancowy. Konczy prace".format(self.sm.name))
                        break

                # czytaj czujniki, jesli krancowka zwarta wyslij wiadomosc i zakoncz program
                if self.smc_read_sensor(self.sm_sensor):
                    logger.debug("{} Wyslij wiadomosc czujnik krancowy. Koncz prace".format(self.sm.name))
                    wiadomosc_lock.acquire()
                    wiadomosc = -1
                    wiadomosc_lock.release()
                    break

                # ustawienie flagi decydujacej o przyspieszeniu lub zwolnieniu
                if krok > polowa_krokow:
                    flaga_czy_przyspieszamy = 0

                # oblicznie opoznienia dla przyspiezsenia
                if flaga_czy_przyspieszamy == 1:
                    nr_kroku += 1
                    opoznienie = self._smc_ramp_up(nr_kroku, opoznienie)  
                # obliczanie opoznienia czasowego dla zwolnienia
                elif flaga_czy_przyspieszamy == 0:
                    nr_kroku -= 1
                    opoznienie = self._smc_ramp_down(nr_kroku, opoznienie)

                # wykonanie pierwszego kroku z najnizsza zdefiniowana predkoscia
                if krok == 0:
                    opoznienie = self.acc_time_low

                # sprawdz czy opoznienie jest najmniejsze (najwieksza predkosc)
                if opoznienie <= self.acc_time_high:
                    logger.debug("{} step {}, counter {}, delay {}".format(self.sm.name, krok, nr_kroku, self.acc_time_high))
                    self._smc_set_step(self.acc_time_high)
                else:
                    logger.debug("{} step {}, counter {}, delay {}".format(self.sm.name, krok, nr_kroku, round(opoznienie,7)))
                    self._smc_set_step(round(opoznienie,7))

        elif ilosc_krokow_do_wykonania < 0:
            logger.error("{} Number of steps must be higher than 0, not {}".format(self.sm.name, ilosc_krokow_do_wykonania))

    def smc_move_scara(self, kierunek1, ilosc_krokow_do_wykonania1, kierunek2, ilosc_krokow_do_wykonania2, wiadomosc, wiadomosc_lock):
        '''
        Zmodyfikowana wersja smc_move pozwalająca na przechodzenie przez środkowy punkt trasy.
        W ten sposób ramie przemieszcza się po krótszej lini i unikamy kolizji z miejscami zabronionymi.
        '''
        # ustaw kierunek obrotow silnika
        if kierunek1 == kierunek2:
            self._smc_set_direction(kierunek1)
            ilosc_krokow_do_wykonania = ilosc_krokow_do_wykonania1 + ilosc_krokow_do_wykonania2
            self.smc_move(kierunek1, ilosc_krokow_do_wykonania, wiadomosc, wiadomosc_lock)

        elif kierunek1 != kierunek2:
            self.smc_move(kierunek1, ilosc_krokow_do_wykonania1, wiadomosc, wiadomosc_lock)
            self.smc_move(kierunek2, ilosc_krokow_do_wykonania2, wiadomosc, wiadomosc_lock)

