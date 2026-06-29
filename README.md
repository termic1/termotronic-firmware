# termotronic-firmware
versions of diferent boards firmware
to clone the project, use:
- git clone https://github.com/termic1/termotronic-firmware.git
- cd termotronic-firmware
- python3 main.py

modify crontab to start the programmer at power-up. add the following line to crontab with:
- crontab -e
- add:
- PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games
- @reboot sleep30; DISPLAY=:0   /home/orangepi/prende.sh > /home/orangepi/prendeout.txt  $t.txt  2> /home/orangepi/prendeerr.txt

Copy the following files to the root directory: orangepi
- prende.sh
- pren.log
- prendeerr.txt
