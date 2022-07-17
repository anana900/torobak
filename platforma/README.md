# Raspberry

## Raspbian Lite OS

### Pobranie i instalacja
Pobieramy ze strony https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&ved=2ahUKEwjvxLXV5f_4AhXhAhAIHUVxDawQFnoECBYQAQ&url=https%3A%2F%$
Następnie instalujemy na karcie SD.
### Modyfikacja ustawień systemowych
Nie usuwamy jeszcze karty - modyfikujemy ustawienia systemowe Raaspbian Lite na obecnym hoście.
- interfaces
```sh
nano -c /etc/network/interfaces
```
i modyfikujemy zawartość głównie o część wireless-power off
```sh
# interfaces(5) file used by ifup(8) and ifdown(8)

# Please note that this file is written to be used with dhcpcd
# For static IP, consult /etc/dhcpcd.conf and 'man dhcpcd.conf'

# Include files from /etc/network/interfaces.d:
source-directory /etc/network/interfaces.d

auto lo
iface lo inet loopback
wireless-power off
```
- wpa_supplicant
```sh
nano -c /etc/wpa_supplicant/wpa_supplicant.conf
```
i modyfikujemy zawartość poprzez dodanie bezprzewoeowego interfejsu sieciowego.
Jeśli SSID sieci jest ukryte obowiązkowo scan_ssid=1
```sh
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=PL

network={
    scan_ssid=1
    ssid="nazwa_sieci"
    psk="haslo"
}
```
- ssh

W katalogu boot tworzymy pusty plik ssh - to aktywuje server SSH który jest dostępny na Raspbian Lite ale domyślnie deaktywowany w celach bezpieczeństwa.
```sh
touch ssh
```
Następnie modyfikujemy ustawienia SSH
```sh
nano -c /etc/ssh/sshd_config
```
i na końcu pliku dodajemy linię
```sh
IPQoS cs0 cs0
```
to zapobiegnie potencjalnym problemom z zawieszaniem się sesji ssh

### Uruchomienie Raspbian Lite i podstawowa konfiguracja
Wkładamy SD do Raspberry i zasilamy urządzenie
Łączymy się poprzez sesję SSH:
```sh
ssh pi@raspberrypi.local
```
gdzie pi to dymyślna nazwa użytkownika, a raspberrypi to domyślna nazwa hosta raspberry. raspberrypi.local zwraca IP adres. Hasło domyślne to raspberrypi.
Uruchamiamy konfigurator w celu zmienienia ustawień systemowych:
```sh
sudo raspi-config
```
- hasło
- konfiguracje lokalizacji i języka
- aktywowania interfejsów: I2C etc.
- etc.

## Git
```sh
sudo apt install git
```
### Ustawienie wysyłania zmian bez hasła do github
```sh
git config --global credential.helper store
git config credential.helper store
git push https://github.com/repo.git
```
zapyta tylko tym razem potem wysyłanie będzie bez konieczności podawania hasła.

