# External module imports
import RPi.GPIO as GPIO
import time
from picamera import PiCamera
from subprocess import call
import datetime
import os
import glob
from urllib2 import urlopen


camera = PiCamera()

# Pin Definitons:
greenPin = 18 # Broadcom pin 18 (P1 pin 12)
bluePin = 23 # Broadcom pin 23 (P1 pin 16)
butPin = 17 # Broadcom pin 17 (P1 pin 11)
counter = 1
timer = 0 # timer for taking picture
state = 0 # 0 idle, 1 taking pictures 
frame = 1 # frame counter
datestamp = "" 
framesize = 2 # seconds between each picture

# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(bluePin, GPIO.OUT) # LED pin set as output
GPIO.setup(greenPin, GPIO.OUT) # PWM pin set as output
GPIO.setup(butPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin set as input w/ pull-up

# Initial state for LEDs:
GPIO.output(bluePin, GPIO.LOW)
GPIO.output(greenPin, GPIO.LOW)

print("Here we go! Press CTRL+C to exit")

try:
	while 1:
		
	# if currently active	
	if state == 1:
		GPIO.output(bluePin, GPIO.HIGH)
		if time.time()-timer >= framesize:
			GPIO.output(greenPin, GPIO.HIGH)
			print ("Taking picture: %d" % frame)
			camera.capture('/home/pi/frames/%s-frame%04d.jpg' % (datestamp,frame))
			frame += 1
			time.sleep(0.1)
			GPIO.output(greenPin, GPIO.LOW)
			timer = time.time()
	else:
		GPIO.output(bluePin, GPIO.LOW)

	if not GPIO.input(butPin): # button is pressed
		
		print("button pressed")

		if state == 0: # start print, taking pictures 
			urlopen("http://192.168.1.77:8082/json.htm?type=command&param=switchlight&idx=95&switchcmd=On")
			timer = time.time()
			state = 1
			now = datetime.datetime.now()
			datestamp = "%d%02d%02d-%02d%02d" % (now.year, now.month,now.day,now.hour,now.minute)
			print(datestamp)

		else: # stop taking pictures, convert and send movie
			frames_link = "/home/pi/frames/%s-frame%%04d.jpg" % datestamp
			movie_link = "/home/pi/movies/print-%s.mp4" % datestamp
			call (["avconv","-f","image2","-i",frames_link,movie_link])
			call (["scp",movie_link,"bjorn@192.168.1.99:Dropbox/Maker/3D/Movies"])				
			files = glob.glob('/home/pi/frames/*')
			for f in files:
				os.remove(f)
			
			state = 0
			urlopen("http://192.168.1.77:8082/json.htm?type=command&param=switchlight&idx=95&switchcmd=Off")

		time.sleep(0.5)

except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
	GPIO.cleanup() # cleanup all GPIO

