import board
import busio
import adafruit_vl53l0x
from time import sleep


class PomiarOdleglosci:
    def __init__(self):
        self.i2c  = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_vl53l0x.VL53L0X(self.i2c)
        # sensor.measurement_timing_budget = 33000

    def pomiar_odleglosci_mm(self):
        return self.sensor.range

def test_pomiar():
    po = PomiarOdleglosci()
    while True:
        print(f"{po.pomiar_odleglosci_mm()}")
        sleep(0.1)

if __name__ == '__main__':
    test_pomiar()
