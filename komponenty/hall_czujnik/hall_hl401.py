"""
Testowanie czujnika hall'a w celu zastosowania go do odczytywania ilości obrótów w silnikach DC.

Obserwacja: czujnik w zależności od położenia/ sposobu przesunięcia magnesu może zmienić permamentnie
z 0 na 1 lub z 1 na 0. Możliwe że magnes kórego używam wytwarza podówje pole które generuje 2 impulsy,
ale czasami wygeneruje tylko 1 podczas przesunięcia i obserwowany jest taki efekt. Do sprawdzenia z
innymi magnesami.

Rozpiska wyprowadzeń RPI3
 +-----+-----+---------+------+---+---Pi 3---+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 |     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
 |   2 |   8 |   SDA.1 | ALT0 | 1 |  3 || 4  |   |      | 5v      |     |     |
 |   3 |   9 |   SCL.1 | ALT0 | 1 |  5 || 6  |   |      | 0v      |     |     |
 |   4 |   7 | GPIO. 7 |   IN | 1 |  7 || 8  | 0 | IN   | TxD     | 15  | 14  |
 |     |     |      0v |      |   |  9 || 10 | 1 | IN   | RxD     | 16  | 15  |
 |  17 |   0 | GPIO. 0 |   IN | 0 | 11 || 12 | 0 | IN   | GPIO. 1 | 1   | 18  |
 |  27 |   2 | GPIO. 2 |   IN | 0 | 13 || 14 |   |      | 0v      |     |     |
 |  22 |   3 | GPIO. 3 |   IN | 0 | 15 || 16 | 0 | IN   | GPIO. 4 | 4   | 23  |
 |     |     |    3.3v |      |   | 17 || 18 | 0 | IN   | GPIO. 5 | 5   | 24  |
 |  10 |  12 |    MOSI | ALT0 | 0 | 19 || 20 |   |      | 0v      |     |     |
 |   9 |  13 |    MISO | ALT0 | 0 | 21 || 22 | 0 | IN   | GPIO. 6 | 6   | 25  |
 |  11 |  14 |    SCLK | ALT0 | 0 | 23 || 24 | 1 | OUT  | CE0     | 10  | 8   |
 |     |     |      0v |      |   | 25 || 26 | 1 | OUT  | CE1     | 11  | 7   |
 |   0 |  30 |   SDA.0 |   IN | 1 | 27 || 28 | 1 | IN   | SCL.0   | 31  | 1   |
 |   5 |  21 | GPIO.21 |   IN | 1 | 29 || 30 |   |      | 0v      |     |     |
 |   6 |  22 | GPIO.22 |   IN | 1 | 31 || 32 | 0 | IN   | GPIO.26 | 26  | 12  |
 |  13 |  23 | GPIO.23 |   IN | 0 | 33 || 34 |   |      | 0v      |     |     |
 |  19 |  24 | GPIO.24 |   IN | 0 | 35 || 36 | 0 | IN   | GPIO.27 | 27  | 16  |
 |  26 |  25 | GPIO.25 |   IN | 0 | 37 || 38 | 0 | IN   | GPIO.28 | 28  | 20  |
 |     |     |      0v |      |   | 39 || 40 | 0 | IN   | GPIO.29 | 29  | 21  |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+---Pi 3---+---+------+---------+-----+-----+
https://www.dummies.com/article/technology/computers/hardware/raspberry-pi/raspberry-pi-gpio-pin-alternate-functions-143761/
"""
import RPi.GPIO as GPIO

HALL_BCM = 21
# BCM - opisy pinów zgodnie z płytką
# BOARD - opisy pinów zgodnie z wyprowadzeniami procesora
GPIO.setmode(GPIO.BCM)
GPIO.setup(HALL_BCM, GPIO.IN)   #, pull_up_down=GPIO.PUD_DOWN)

def test_hall_hl401():
    """
    Idea polega na zliczaniu zboczy opadających 1 -> 0.
    Czujnik Hall'a podłączony jest do portu GPIO ustawionego jako wejście.
    Pomocnicza zmienna hall_status_aktualny trzyma informację o aktualnym
    stanie wejścia. Jeśli nastąpi zmiana z 1 -> 0 wówczas zaliczany jest
    impuls. W przypadku braku zmiany 0 -> 0, lub 1 -> 1 sprawdzanie stanu
    GPIO jest kontunuowane. 
    """
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

if __name__=='__main__':
    try:
        test_hall_hl401()
    except KeyboardInterrupt:
        print("Zakonczenie poprzez ctrl+c")
    except Exception as unknown_exception:
        print(f"To nie powinno sie wydarzyc! {unknown_exception:}")
    finally:
        print("Czyszczenie GPIO")
        GPIO.cleanup()

