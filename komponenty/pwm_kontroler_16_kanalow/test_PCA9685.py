# https://circuitpython.readthedocs.io/projects/servokit/en/latest/
import time

from adafruit_servokit import ServoKit

# dla MG90s czasy dla PWD wynoszą od 500us do 2500us, zakres 180, czas przejscia od 0 do 180 300ms
MIN_IMP  =[500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500]
MAX_IMP  =[2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500]
MIN_ANG  =[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
MAX_ANG  =[180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180]

nbPCAServo=16
pca = ServoKit(channels=nbPCAServo)

def konfiguracja_pca() -> None:
    for i in range(nbPCAServo):
        pca.servo[i].set_pulse_width_range(MIN_IMP[i] , MAX_IMP[i])

def test_pca() -> None:
    kat_skok = 1
    oponienie_s = 0.002
    for i in range(nbPCAServo):
        print(f"Sprawdzenie ze skokiem {kat_skok}")
        i = 0
        for j in range(MIN_ANG[i], MAX_ANG[i], kat_skok):
            pca.servo[i].angle = j
            time.sleep(opoznienie_s)
        for j in range(MAX_ANG[i], MIN_ANG[i], -kat_skok):
            pca.servo[i].angle = j
            time.sleep(opoznienie_s)
        pca.servo[i].angle=None # disable channel
        time.sleep(3)

def chwytak(zacisnij_bool: bool) -> None:
    kat_rozwarcia = 22
    opoznienie_s = 0.002
    if zacisnij_bool:
        for kat in range(0, kat_rozwarcia, 1):
            pca.servo[0].angle = kat
            time.sleep(opoznienie_s)
    else:
        for kat in range(kat_rozwarcia, 0, -1):
            pca.servo[0].angle = kat
            time.sleep(opoznienie_s)

def test_chwytak() -> None:
    przerwa_s = 0.05
    counter_single_move = 0
    status=False
    while True:
        status = False if status else True
        chwytak(status)
        time.sleep(przerwa_s)
        counter_single_move += 1
        if not counter_single_move % 100:
            print(counter_single_move)

if __name__ == '__main__':
    konfiguracja_pca()
    #test_pca()
    test_chwytak()
