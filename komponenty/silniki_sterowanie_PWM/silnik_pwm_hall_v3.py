"""
Obroc silnik o zadana ilosc impulsow.

Test silnika 12V i zintegrowanego czujnika hall'a A87L (A3187LUA).
Czujnik https://www.digchip.com/datasheets/parts/datasheet/029/A3187LUA-pdf.php
Rezystor R0 jest wbudowany w złącze silnika. R1 jest dołożony zewnętrznie.
             ^ Vcc
             |
            ---
            | | R1 10k
            ---
             |____________out to uC
             |
            ---
            | | R0 330 
            ---
             |
             /
Motor      |/
Magnet --> |    A87L
           |\
             V
             |
            gnd

Złącze silnika rozpiska
.2  .3  -5
.1  .4  -6
1 Vcc hall
2 GND hall
3 Out hall
4 NC
5 motor
6 motor

Magnes silnika ma 2 bieguny S i 2 bieguny N rozmieszczone naprzemiennie:
    S
N       N
    S
to sprawia że czujnik Hall'a na 1 obrót magnesu wytwarza ciąg sygnału: 0101.

PROBLEM 1
Okazuje się ze czytanie z czujnika halla jest bardzo powolne.
Zmienia się w zaleznosci od przylozonego napiecia do ukladu sterownika.
Silnik 12V, wbudowany czujnik Hall'a A78L.
Dla 12V
30 impulsów czyta 40
50 impulsów czyta 65
Dla 5V
30 impulsów czyta 30
50 impulsów czyta 50

PROBLEM 2
Przy zasilaniu 12V sterownik nie wspolpracuje z silnikiem 12V poprawnie. Zdarza się to losowo.
Jakby wzbudzenie. Wyłączenie zasilania na kilka s pomaga. Do sprawdzenia.
Problem występuje też przy innych zasilaniach.
Możliwe że to kwestia zkłeceń od silnika do sterownika. Po odsunięciu samego silnika problem ustał.
Wzbudzenia powodowane sa rowniez zbyt niska wartoscia przyspieszenia z zakresu -1 do 1, dlatego 
stosuje wartosci od 0 do 1.

PROBLEM 3
Niedokładność przesunięcia silnika.
Niedokladnosc z przesunieciem silnika jest zwiazana z bezwladnoscia.
Moznaby to SW rozwiazac, ale to doklada dodatkowy czas na ustawienie pozycji silnika.
Na ta chwile mysle ze dokladnosc nie jest wazna.
"""
import time

import RPi.GPIO as GPIO
from adafruit_servokit import ServoKit

from threading import Thread, Lock, Event

# BCM - opisy pinów zgodnie z płytką
# BOARD - opisy pinów zgodnie z wyprowadzeniami procesora
GPIO.setmode(GPIO.BCM)

# Konfiguracja do płytki sterownika PWM
serwo_ilosc_kanalow = 16
pca = ServoKit(channels = serwo_ilosc_kanalow)

# Konfiguracja do czujnika HALL
HALL_BCM = 21
GPIO.setup(HALL_BCM, GPIO.IN)

# Event do zatrzymywania pracy watkwo w przypadku ctrl+c
event_stop = Event()

def czujnik_hall(zadane_obroty_lock) -> None:
    """
    Zlicza zbocza z czujnika halla.
    """
    print("Watek hall start")
    global zadane_obroty
    hall_tick_counter = 0
    hall_status = GPIO.input(HALL_BCM)
    while True:
        if event_stop.is_set():
            break
        hall_status_now = GPIO.input(HALL_BCM)
        if hall_status != hall_status_now:
            hall_status =  hall_status_now
            hall_tick_counter += 1
            with zadane_obroty_lock:
                zadane_obroty -= 1
    print(f"zadane obroty {zadane_obroty} hall_counter {hall_tick_counter}")
    print("Watek hall stop")

serwo_ilosc_kanalow = 16
pca = ServoKit(channels = serwo_ilosc_kanalow)

def silnik_pwm(port_lewo: int, port_prawo: int, kierunek, zadane_obroty_lock) -> None:
    print("Watek silnik start")
    global zadane_obroty
    min_szerokosc_pulsu_us = 0
    max_szerokosc_pulsu_us = 19900  # dobrane experymentalnie
    pca.continuous_servo[port_lewo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)
    pca.continuous_servo[port_prawo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)
    acceleration = [-1, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

    acc = 0
    while zadane_obroty > 0:
        if event_stop.is_set():
            break
        if zadane_obroty > 25 and acc < 0.9:
            acc += 0.1
        if zadane_obroty - 25 <= 0 and acc > 0:
            acc -= 0.1
        if kierunek:
            pca.continuous_servo[port_lewo].throttle = acc
        else:
            pca.continuous_servo[port_prawo].throttle = acc
    pca.continuous_servo[port_lewo].throttle = -1
    pca.continuous_servo[port_prawo].throttle = -1
    event_stop.set()
    print(f"zadane obroty {zadane_obroty}")
    print("Watek silnik stop")

zadane_obroty = 2
def silnik_sterowanie() -> None:
    global zadane_obroty
    kierunek = 0
    zadane_obroty_lock = Lock()
    try:
        while True:
            kierunek = 0 if kierunek else 1
            watek_silnik_czujnik_hall = Thread(target=czujnik_hall, args=(zadane_obroty_lock,))
            watek_silnik_pwm = Thread(target=silnik_pwm, args=(14, 15, kierunek, zadane_obroty_lock,))
            watek_silnik_czujnik_hall.start()
            watek_silnik_pwm.start()
            watek_silnik_czujnik_hall.join()
            watek_silnik_pwm.join()
            time.sleep(1)
            event_stop.clear()
            zadane_obroty = 2
    except KeyboardInterrupt:
        print("Zakonczenie poprzez ctrl+c")
        event_stop.set()
    except Exception as unknown_exception:
        print(f"To nie powinno sie wydarzyc! {unknown_exception:}")
    finally:
        print("Czyszczenie GPIO!")
        pca_cleanup(14, 15)
        GPIO.cleanup()

def pca_cleanup(port_lewo: int, port_prawo: int) -> None:
    """
    Czyszczenie
    """
    pca.continuous_servo[port_prawo].throttle = -1
    pca.continuous_servo[port_lewo].throttle = -1

if __name__=='__main__':
    silnik_sterowanie()
