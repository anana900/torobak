"""
obroc silnik o zadana ilosc impulsow.

"""
import time

import RPi.GPIO as GPIO
from adafruit_servokit import ServoKit

from threading import Thread, Lock, Event

HALL_BCM = 21
# BCM - opisy pinów zgodnie z płytką
# BOARD - opisy pinów zgodnie z wyprowadzeniami procesora
GPIO.setmode(GPIO.BCM)
GPIO.setup(HALL_BCM, GPIO.IN)

event_stop = Event()

def silnik_hall(zadane_obroty_lock) -> None:
    global zadane_obroty
    hall_status_aktualny = 0
    licznik = 1
    while licznik:
        hall_status = GPIO.input(HALL_BCM)
        if hall_status == 0 and hall_status_aktualny == 1:
                hall_status_aktualny = hall_status
                with zadane_obroty_lock:
                    zadane_obroty -= 1
                    licznik = zadane_obroty
                    print(f"licznik {licznik}")
        elif hall_status == 1 and hall_status_aktualny == 0:
                hall_status_aktualny = hall_status
        if event_stop.is_set():
            break
    print("konczymy watek HALL")

serwo_ilosc_kanalow = 16
pca = ServoKit(channels = serwo_ilosc_kanalow)

def silnik_pwm(port_lewo: int, port_prawo: int, kierunek, zadane_obroty_lock) -> None:
    global zadane_obroty
    min_szerokosc_pulsu_us = 0
    max_szerokosc_pulsu_us = 1e4
    pca.continuous_servo[port_lewo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)
    pca.continuous_servo[port_prawo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)
    bezwladnosc_czasowa_s = 0.075
    przyspieszenie_start = 0    # -10 - 10
    przyspieszenie_stop = 10    # -10 - 10
    przyspieszenie_krok = 2     # > 0
    przyspieszenie_dzielnik = 10

    while True:
        with zadane_obroty_lock:
            print(f"silnik {zadane_obroty}")
            if zadane_obroty <= 0:
                break
        if kierunek:
            pca.continuous_servo[port_lewo].throttle = 0.1
        else:
            pca.continuous_servo[port_prawo].throttle = 0.1
        if event_stop.is_set():
            break
        time.sleep(0.1)

    pca.continuous_servo[port_lewo].throttle = -1
    pca.continuous_servo[port_prawo].throttle = -1
    print("konczymy watek silnik")


zadane_obroty =5
def silnik_sterowanie() -> None:
    zadane_obroty_lock = Lock()
    try:
        watek_silnik_czujnik_hall = Thread(target=silnik_hall, args=(zadane_obroty_lock,))
        watek_silnik_pwm = Thread(target=silnik_pwm, args=(14, 15, 1, zadane_obroty_lock,))
        watek_silnik_czujnik_hall.start()
        watek_silnik_pwm.start()
        watek_silnik_czujnik_hall.join()
        watek_silnik_pwm.join()
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
