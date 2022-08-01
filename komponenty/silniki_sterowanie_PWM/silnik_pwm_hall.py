import time

import RPi.GPIO as GPIO
from adafruit_servokit import ServoKit

from threading import Thread

HALL_BCM = 21
# BCM - opisy pinów zgodnie z płytką
# BOARD - opisy pinów zgodnie z wyprowadzeniami procesora
GPIO.setmode(GPIO.BCM)
GPIO.setup(HALL_BCM, GPIO.IN)

def silnik_hall() -> None:
    hall_status_aktualny = 0
    licznik = 0
    while True:
        hall_status = GPIO.input(HALL_BCM)
        if hall_status == 0 and hall_status_aktualny == 1:
                hall_status_aktualny = hall_status
                licznik += 1
                print(f"puls {licznik}")
        elif hall_status == 1 and hall_status_aktualny == 0:
                hall_status_aktualny = hall_status


serwo_ilosc_kanalow = 16
pca = ServoKit(channels = serwo_ilosc_kanalow)

def silnik_pwm(port_lewo: int, port_prawo: int,
                              min_szerokosc_pulsu_us: int=0, max_szerokosc_pulsu_us: int=1e4) -> None:
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

        pca.continuous_servo[port_prawo].throttle = -1
        pca.continuous_servo[port_lewo].throttle = -1

def silnik_sterowanie() -> None:
    try:
        watek_silnik_czujnik_hall = Thread(target=silnik_hall, args=())
        watek_silnik_pwm = Thread(target=silnik_pwm, args=(14, 15,))
        watek_silnik_czujnik_hall.start()
        watek_silnik_pwm.start()
        watek_silnik_czujnik_hall.join()
        watek_silnik_pwm.join()
    except KeyboardInterrupt:
        print("Zakonczenie poprzez ctrl+c")
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
