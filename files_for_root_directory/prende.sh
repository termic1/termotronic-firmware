#!/bin/bash
echo $PATH
export DISPLAY=:0.0
echo "entro al .sh"
python3 /home/orangepi/termotronic-firmware/main.py #not compiled version
#cd /home/orangepi/termotronic-firmware ./main  #compiled version
echo "Arranco el programador exitosamenmte"
