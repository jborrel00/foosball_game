"""foosball_game.py 
this program will be run on the raspberry pi while the foosball game is going on. it will read the two card IDs of the players
as well as the sides the players are playing on. this program is designed to work with the arduino program
NFC-Card-Trigger.ino

additionally, this program will, once the player and side information has been input, keep track of goals and, at the
game's conclusion, update the necessary mysql tables."""

import RPi.GPIO as GPIO
import serial
import MySQLdb as mdb
from time import sleep
import glob

GPIO.setwarnings = False
GPIO.setmode(GPIO.BOARD)
GPIO.setup(5,GPIO.OUT)
left_goal = GPIO.setup(11,GPIO.IN) #left goal photosensor
left_goal2 = GPIO.setup(13,GPIO.IN) #optional second left goal photosensor
right_goal = GPIO.setup(16,GPIO.IN) #right goal photosensor
right_goal2 = GPIO.setup(18,GPIO.IN) #optional second right goal photosensor
hand_slot_l = GPIO.setup(21,GPIO.IN) #left goal hand slot
hand_slot_r = GPIO.setup(22,GPIO.IN) #right goal hand slot

GPIO.output(5,0)
sleep(.1)
GPIO.output(5,1)

if '/dev/ttyACM1' in glob.glob('/dev/tty*'):
	ser = serial.Serial('/dev/ttyACM1',115200)
else:
	ser = serial.Serial('/dev/ttyACM0',115200)
while true:
	i = 0
	j = 0
	#card-reading while loop
	while i == 0:
		#vars
		p = []
		q = []
		s = []

		con = mdb.connect('localhost','root','foosball','foosball')
		with con:
			cur = con.cursor()
			cur.execute('select Id, playerID from name_hex_data')
				rows = cur.fetchall()
			for row in rows:
				p.append(row[0])
				q.append(row[1])
				print p #debugging

		GPIO.output(5,0)
		sleep(.1)
		GPIO.output(5,1)
		print "reading..."
		for a in range(3): #3 lines will be coming to the pi, side, p1 card ID and p2 card ID
			r = ser.readline()
			#may need to save s[0] sooner, in case the other things we're doing to the array won't work for the string
			s.append(rstrip().rstrip('.').replace(" ", ""))
			#s[0] is the string that says what side p1 is on - "left" or "right"
			#s[1] is the card ID of player 1
			#s[2] is the card ID of player 2
			print s[0] #debugging
			print s[1] #debugging
			print s[2] #debugging

		if s[1] in p: #checking to make sure player's card's ID is in the database
			print 'exists in name_hex_data'
			j += 1
		else:
			print 'you must register your card at the kiosk'
		if s[2] in p: #checking to make sure player's card's ID is in the database
			print 'exists in name_hex_data'
			if s[2] == s[1]:
				print 'you can\'t play yourself!'
			else:	
				j += 1
		else:
			print 'you must register your card at the kiosk'
		if j == 2:
			i = 1
		if j < 2:
			print 'rechecking database'
			i = 0
	s[1] = q[int(s[1],16)-1]
	s[2] = q[int(s[2],16)-1]

	print 'let the game begin!'
	#score-keeping while loop
	score1 = 0
	score2 = 0
	while score1 < 10 and score2 < 10:
		while hand_slot_r == 1 and hand_slot_l == 1: #assuming 1 when laser is not obstructed
		"""need to factor in player's choice of sides. player 1 doesn't have to choose left"""
			if left_goal == 0: #assuming 0 when the laser is obstructed
			#also, may change to left_goal and left_goal2
				score1 += 1
				print score1 #debugging
				sleep(1)
			if right_goal == 0:
				score2 += 1
				print score2 #debugging
				sleep(1)
		while hand_slot_l == 0 or hand_slot_r == 0:
			if left_goal == 0: 
				score1 += 0
				print 'get your hand out of the goal!'
			if right_goal == 0:
				score2 += 0
				print 'get your hand out of the goal!'
	print 'game over!'

	#sending game data to mysql
	cur = con.cursor()
	cur.execute("insert into game_info (player1,score1,player2,score2) values("+s[1]+","+score1+","+s[2]+","+score2+")")
	if score1 == 10:
		cur.execute("update name_game_data set wins = wins + 1 where playerID = " +s[1])
		cur.execute("update name_game_data set losses = losses + 1 where playerID = " +s[2])
	else:
		cur.execute("update name_game_data set wins = wins + 1 where playerID = " +s[2])
		cur.execute("update name_game_data set losses = losses + 1 where playerID = " +s[1])
	con.close()	
