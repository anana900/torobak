import time
import RPi.GPIO as GPIO
from adafruit_servokit import ServoKit

nbPCAServo=16
pca = ServoKit(channels=nbPCAServo)

def test_silnik_dc_1(port_lewo: int, port_prawo: int, min_szerokosc_pulsu_us: int=0, max_szerokosc_pulsu_us: int=1e4) -> None:
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

def test_silnik_dc_2(port_lewo: int, port_prawo: int, min_szerokosc_pulsu_us: int=0, max_szerokosc_pulsu_us: int=1e4) -> None:
    """
    Przyspieszenie realizowane jest pprzez manipulacje wartosci throttle z klasy continuous servo.
    """
    pca.continuous_servo[port_lewo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)
    pca.continuous_servo[port_prawo].set_pulse_width_range(min_szerokosc_pulsu_us, max_szerokosc_pulsu_us)

    bezwladnosc_czasowa_s = 1
    # throttle akceptuje wartosci od -1.0 do 1.0, ale na cele uzycia w range zmieniam skale
    # od -10 do +10 z krokiem 1
    przyspieszenie_start = -10
    przyspieszenie_stop = 10
    przyspieszenie_krok = 2
    przyspieszenie_dzielnik = 10
    while True:
        for i in range(przyspieszenie_start, przyspieszenie_stop+1, przyspieszenie_krok):
            # Petla przyspieszenia lewo
            pca.continuous_servo[port_lewo].throttle = i/przyspieszenie_dzielnik
            time.sleep(bezwladnosc_czasowa_s)
        pca.continuous_servo[port_lewo].throttle = -1
        print("Lewo ok")
        time.sleep(1)
        for i in range(przyspieszenie_start, przyspieszenie_stop+1, przyspieszenie_krok):
            # Petla przyspieszenia prawo
            pca.continuous_servo[port_prawo].throttle = i/przyspieszenie_dzielnik
            time.sleep(bezwladnosc_czasowa_s)
        print("Prawo ok")
        pca.continuous_servo[port_prawo].throttle = -1
        time.sleep(1)

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
        #test_silnik_dc_1(14, 15)
        test_silnik_dc_2(14, 15)
    except KeyboardInterrupt:
        print("Zakonczenie poprzez ctrl+c")
    except Exception as unknown_exception:
        print(f"To nie powinno sie wydarzyc! {unknown_exception:}")
    finally:
        print("Czyszczenie GPIO")
        pca_cleanup(14, 15)
        GPIO.cleanup()

