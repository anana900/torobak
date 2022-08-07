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

PROBLEM 3
Niedokładność przesunięcia silnika.
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

def silnik_hall(zadane_obroty_lock) -> None:
    print("Start watek HALL")
    global zadane_obroty
    hall_status_aktualny = 0
    licznik = 0
    # Pierwsze zczytanie zmiennej globalnej
    with zadane_obroty_lock:
       licznik = zadane_obroty
    while licznik > 0:
        if licznik <=0 or event_stop.is_set():
            break
        hall_status = GPIO.input(HALL_BCM)
        if hall_status == 0 and hall_status_aktualny == 1:
                hall_status_aktualny = hall_status
                with zadane_obroty_lock:
                    zadane_obroty -= 1
                    licznik = zadane_obroty
                    #print(f"licznik {licznik}")
        elif hall_status == 1 and hall_status_aktualny == 0:
                hall_status_aktualny = hall_status
    print("konczymy watek HALL")

serwo_ilosc_kanalow = 16
pca = ServoKit(channels = serwo_ilosc_kanalow)

def silnik_pwm(port_lewo: int, port_prawo: int, kierunek, zadane_obroty_lock) -> None:
    def oblicz_przyspieszenie(obroty: int, kroki: int=10) -> list:
        # Tworzenie tablicy przyśpieszenia
        # Wartości muszą być dobrane pod dany silnik
        przyspieszenie = []
        if obroty < 20:
            przyspieszenie = [0.1 for _ in range(obroty)]
        else:
            przyspieszenie = [round(0.1 * i, 1) for i in range(1, 11)]
            przyspieszenie.extend([1 for _ in range(obroty-20)])
            przyspieszenie.extend([round(1 - i/10, 1) for i in range(0, 10)])
        print(f"obroty {obroty} elementy {len(przyspieszenie)} {przyspieszenie}")
        return przyspieszenie

    print("Start watek silnik")
    global zadane_obroty

    # Konfiguracja sterownika PWM w celu sterowania sterownikiem silnika DC
    min_szerokosc_pulsu_us = 0
    max_szerokosc_pulsu_us = 1e4
    pca.continuous_servo[port_lewo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)
    pca.continuous_servo[port_prawo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)

    # Pierwsze zczytanie zmiennej globalnej
    obroty = 0
    with zadane_obroty_lock:
        obroty = zadane_obroty

    # Tablica przyspieszenia
    przyspieszenie = oblicz_przyspieszenie(obroty)

    # Pętla silnika
    while obroty > 0:
        with zadane_obroty_lock:
            obroty = zadane_obroty
        #print(f"silnik {obroty}")
        if obroty <= 0 or event_stop.is_set():
            break
        if kierunek:
            pca.continuous_servo[port_lewo].throttle = przyspieszenie[obroty - 1]
        else:
            pca.continuous_servo[port_prawo].throttle = przyspieszenie[obroty - 1]
        # uśpienie na 1ms. Przy 12V częstotliwość zmiany sygnału z czujnika A78L ~200Hz co pozwala
        # sprawdzić czujnik ok 5 razy zanim zmieni stan.
        #time.sleep(0.001)

    # Zatrzymywanie silnika
    pca.continuous_servo[port_lewo].throttle = -1
    pca.continuous_servo[port_prawo].throttle = -1
    print("konczymy watek silnik")

zadane_obroty = 21
def silnik_sterowanie() -> None:
    global zadane_obroty
    kierunek = 0
    zadane_obroty_lock = Lock()
    try:
        while True:
            kierunek = 0 if kierunek else 1
            watek_silnik_czujnik_hall = Thread(target=silnik_hall, args=(zadane_obroty_lock,))
            watek_silnik_pwm = Thread(target=silnik_pwm, args=(14, 15, kierunek, zadane_obroty_lock,))
            watek_silnik_czujnik_hall.start()
            watek_silnik_pwm.start()
            watek_silnik_czujnik_hall.join()
            watek_silnik_pwm.join()
            time.sleep(0.2)
            zadane_obroty = 21
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
    Okropne czyszczenie - try/except powinno byc w funkcjach testowych.
    """
    pca.continuous_servo[port_prawo].throttle = -1
    pca.continuous_servo[port_lewo].throttle = -1

if __name__=='__main__':
    silnik_sterowanie()
