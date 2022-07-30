"""
Sprawdzenie sterowanie silnikiem DC poprzez PWM.
Jako sterownik silnika został użyty MX1508 oraz TA6586, do niego podłączony mały silniczek DC.
MX1508 sterowany jest z 2 kanałów PWM (lewo, prawo) z układu PCA9685.

Sprawdzone zostały 2 metody sterowania:
1 zmian wartości angle - tak jek to jest robione w serwomechanizmach.
2 zmiana wartości throttle z klasy continous servo bibliteki ServoKit.

TA6586 - do 5A w pracy ciągłej, 12V, 1 kanał. Płytka testowa posiada 2 układy, 2 kanały.
Sterowanie poprzez 2 piny PWM prawo/lewo.
MX1508 - do 1A w pracy ciągłem 9V , 2 kanały. Płytka testowa posiada 1 układ, 2 kanały.
Sterowanie poprzez 2 piny PWM prawo/lewo.
"""

import time

import RPi.GPIO as GPIO
from adafruit_servokit import ServoKit

nbPCAServo=16
pca = ServoKit(channels=nbPCAServo)

def test_silnik_dc_1_angle(port_lewo: int, port_prawo: int, min_szerokosc_pulsu_us: int=0, max_szerokosc_pulsu_us: int=1e4) -> None:
    """
    Przyspieszenie realizowane jest pprzez manipulacje wartosci angle z klasy Servo.
    set_pulse_width_range ustawiam od 0 us do 1e4 us. Wartosc kata zmieniam od 40 do 100 i
    w ten sposob reguluje przyspieszenie.
    """
    pca.servo[port_lewo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)
    pca.servo[port_prawo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)

    bezwladnosc_czasowa_s = 0.1
    wypenienie_start_procent = 40
    wypenienie_stop_procent = 100
    wypenienie_krok_procent = 5
    while True:
        for i in range(wypenienie_start_procent, wypenienie_stop_procent+1, wypenienie_krok_procent):
            # Petla przyspieszenia lewo
            pca.servo[port_lewo].angle = i
            pca.servo[port_prawo].angle = 0
            time.sleep(bezwladnosc_czasowa_s)
        pca.servo[port_lewo].angle = 0
        print("Lewo ok")
        time.sleep(1)
        for i in range(wypenienie_start_procent, wypenienie_stop_procent+1, wypenienie_krok_procent):
            # Petla przyspieszenia prawo
            pca.servo[port_prawo].angle = i
            pca.servo[port_lewo].angle = 0
            time.sleep(bezwladnosc_czasowa_s)
        print("Prawo ok")
        pca.servo[port_prawo].angle = 0
        time.sleep(1)

def test_silnik_dc_2_throttle(port_lewo: int, port_prawo: int, 
                              min_szerokosc_pulsu_us: int=0, max_szerokosc_pulsu_us: int=1e4) -> None:
    """
    Przyspieszenie realizowane jest poprzez manipulacje wartosci throttle z klasy continuous servo.
    """
    pca.continuous_servo[port_lewo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)
    pca.continuous_servo[port_prawo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)

    bezwladnosc_czasowa_s = 0.075
    # throttle akceptuje wartosci od -1.0 do 1.0, ale na cele uzycia w range zmieniam skale
    # od -10 do +10 z krokiem 1
    przyspieszenie_start = 0    # -10 - 10
    przyspieszenie_stop = 10    # -10 - 10
    przyspieszenie_krok = 2     # > 0
    przyspieszenie_dzielnik = 10
    while True:
        for i in range(przyspieszenie_start, przyspieszenie_stop+1, przyspieszenie_krok):
            # Petla przyspieszenia lewo
            pca.continuous_servo[port_lewo].throttle = i/przyspieszenie_dzielnik
            time.sleep(bezwladnosc_czasowa_s)
        time.sleep(1)
        for i in range(przyspieszenie_stop, przyspieszenie_start-1, -przyspieszenie_krok):
            # Petla przyspieszenia lewo
            pca.continuous_servo[port_lewo].throttle = i/przyspieszenie_dzielnik
            time.sleep(bezwladnosc_czasowa_s)
        pca.continuous_servo[port_lewo].throttle = -1
        print("Lewo ok")
        #time.sleep(1)
        for i in range(przyspieszenie_start, przyspieszenie_stop+1, przyspieszenie_krok):
            # Petla przyspieszenia prawo
            pca.continuous_servo[port_prawo].throttle = i/przyspieszenie_dzielnik
            time.sleep(bezwladnosc_czasowa_s)
        time.sleep(1)
        for i in range(przyspieszenie_stop, przyspieszenie_start-1, -przyspieszenie_krok):
            # Petla przyspieszenia lewo
            pca.continuous_servo[port_prawo].throttle = i/przyspieszenie_dzielnik
            time.sleep(bezwladnosc_czasowa_s)
        print("Prawo ok")
        pca.continuous_servo[port_prawo].throttle = -1
        #time.sleep(1)

def pca_cleanup(port_lewo: int, port_prawo: int):
    """
    Okropne czyszczenie - try/except powinno byc w funkcjach testowych.
    """
    try:
        pca.continuous_servo[port_prawo].throttle = -1
        pca.continuous_servo[port_lewo].throttle = -1
    except:
        pass

    try:
        pca.servo[port_prawo].angle = 0
        pca.servo[port_lewo].angle = 0
    except:
        pass

if __name__=='__main__':
    try:
        #test_silnik_dc_1_angle(14, 15)
        test_silnik_dc_2_throttle(14, 15)
        #test_silnik_dc_2_throttle(14, 15, min_szerokosc_pulsu_us = 2000)
    except KeyboardInterrupt:
        print("Zakonczenie poprzez ctrl+c")
    except Exception as unknown_exception:
        print(f"To nie powinno sie wydarzyc! {unknown_exception:}")
    finally:
        print("Czyszczenie GPIO")
        pca_cleanup(14, 15)
        GPIO.cleanup()
