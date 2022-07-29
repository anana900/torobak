"""
Test dla dwóch urządzeń podpiętych pod I2C: kontroler PWM oraz laserowy czujnik odległości.
"""
import time

import adafruit_vl53l0x
import board
import busio
import RPi.GPIO as GPIO
from adafruit_servokit import ServoKit

# dla MG90s czasy dla PWD wynoszą od 500us do 2500us, zakres 180, czas przejscia od 0 do 180 300ms
MIN_IMP  =[500, 500]
MAX_IMP  =[2500, 2500]
MIN_ANG  =[0, 0]
MAX_ANG  =[180, 180]

class PomiarOdleglosci:
    def __init__(self):
        self.i2c  = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_vl53l0x.VL53L0X(self.i2c)
        # sensor.measurement_timing_budget = 33000

    def pomiar_odleglosci_mm(self):
        return self.sensor.range

def test_multiple_i2c() -> None:
    # konfiguracje servomotorow
    nbPCAServo=16
    pca = ServoKit(channels=nbPCAServo)
    for i in range(nbPCAServo):
        pca.servo[i].set_pulse_width_range(MIN_IMP[i] , MAX_IMP[i])
    serwo_0 = 0
    serwo_1 = 1

    # konfiguracja czujnika odleglosci
    po = PomiarOdleglosci()

    kat_skok = 1
    opoznienie_s = 0.002
    for i in range(nbPCAServo):
        print(f"Odleglosc {po.pomiar_odleglosci_mm()}")
        print(f"Sprawdzenie ze skokiem {kat_skok}")
        for j in range(MIN_ANG[i], MAX_ANG[i], kat_skok):
            pca.servo[serwo_0].angle = j
            pca.servo[serwo_1].angle = j
            time.sleep(opoznienie_s)
        for j in range(MAX_ANG[i], MIN_ANG[i], -kat_skok):
            pca.servo[serwo_0].angle = j
            pca.servo[serwo_1].angle = j
            time.sleep(opoznienie_s)
        pca.servo[serwo_0].angle=None # disable channel
        pca.servo[serwo_1].angle=None # disable channel
        time.sleep(3)

if __name__ == '__main__':
    try:
        test_multiple_i2c()
    except KeyboardInterrupt:
        print("Zakonczenie poprzez ctrl+c")
    except Exception as unknown_exception:
        print(f"To nie powinno sie wydarzyc! {unknown_exception}")
    finally:
        print("Czyszczenie GPIO")
        GPIO.cleanup()
