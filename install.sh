#!/bin/sh

# Install the files on a pico
if [ -z "$1" ]
  then
    echo "/dev/ttyACMx parameter missing!"
                exit 0
fi

CUR_DIR=`pwd`
LIB_DIR="/home/domeu/python/esp8266-upy"

# Install the files on a MicroPython board

mpremote connect $1 fs mkdir lib

# --- Remote library ---
mpremote connect $1 mip install github:mchobby/esp8266-upy/lcdi2c
mpremote connect $1 mip install github:mchobby/esp8266-upy/LIBRARIAN
mpremote connect $1 mip install github:mchobby/esp8266-upy/m5stack-u135
mpremote connect $1 mip install github:mchobby/esp8266-upy/max31855
#mpremote connect $1 fs cp $LIB_DIR/fsr-fma-25N/lib/fsrfma.py :lib/


# --- Local library ---
mpremote connect $1 fs cp lib/*.py :lib/


#mpremote connect $1 fs cp main.py :
mpremote connect $1 fs cp boot.py :
mpremote connect $1 fs cp main.py :

# Set the MCU datetime
mpremote connect $1 rtc --set
