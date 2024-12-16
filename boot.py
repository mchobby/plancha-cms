from machine import Pin
# Make sure that SSR Relay is off when restarting
Pin(13, Pin.OUT, value=False)
# Stop Cooling
Pin(19, Pin.OUT, value=False)