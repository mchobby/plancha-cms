from machine import Pin, I2C
from i2cenc import I2CEncoder
from time import sleep

i2c = I2C( 0, sda=Pin.board.GP8, scl=Pin.board.GP9, freq = 100000 )
print( i2c.scan())

enc = I2CEncoder(i2c)

print( "Testing the LEDs" )
enc.color = (255,0,0) # Rouge
sleep( 0.5 )
enc.color = (0,255,0) # Vert
sleep( 0.5 )
enc.color = (0,0,255) # Bleu
sleep( 1 )
#enc.color = (0,0,0) # Eteint

last_v = 0
while True:
	if enc.button: # Est-ce que le bouton est actuellement pressé ?
		print( 'Button PRESSE')
		enc.position = 0 # Réinitialiser le comtpeur - ne fonctionne pas!

	v = enc.position # -32768 <= v <= 32767
	if v != last_v: # afficher uniquement si valeur changée
		print( v )
		last_v = v
	sleep( 0.05 )