#! /usr/bin/env python

import socket
from time import time
from time import sleep
from atexit import register
from random import randint

sck = socket.socket (socket.AF_INET, socket.SOCK_DGRAM) #primary socket

sck.bind (('',9999))


#change to non-blocking
sck.settimeout(0.04) # 40 ms wait, check 25 times per second 


#global vars

collector = ( socket.gethostbyname('datacollector.no-ip.biz'),9999)
next_aggregator = ()
echodip = ('datacollector.no-ip.biz',14001)
public_address = ''
should_be_aggregator = False

aggs = {}
child_aggs = []

print "Welcome to the Data Aggregation System!\nI will handle everything for you.\nJust sit and watch or go get a drink of water.\n\n"
sleep(5)

def inform_lost ():
	global child_aggs
	print "Informing children aggregators that we lost connectivity with the system."
	for i in range(len(child_aggs)):
		print child_aggs[i]
		sck.sendto('nope',child_aggs[i])
	if should_be_aggregator:
		sck.sendto('aggt',collector) # should de-register
		print "Informing collector to remove us from the aggregator list as well."
	child_aggs = []

register(inform_lost) #best effort attempt to inform children if we exit program

#setup / join

def setup ():
	global aggs, public_address, next_aggregator, sck2, sck, should_be_aggregator
	aggs.clear()
	should_be_aggregator = False
	sck2 = socket.socket (socket.AF_INET, socket.SOCK_DGRAM) #used for setup mostly, to hide source port
	#change to 5 second time out
	sck2.settimeout(5)
	
	# while 1:
		# try:
			# sck.recvfrom(4096)
			# continue
		# except socket.timeout:
			# break
		# except socket.error:
			# break
	
	print "Connecting to the collector's echo IP service to learn our public address."
	sleep(5)
	#get my public ip 	
	rem_msg = ''
	sck2.sendto('',echodip)
	try:
		rem_msg, rem_addr = sck2.recvfrom(4096)
	except (socket.timeout, socket.error):
		print "Problem with UDP echo IP service, cannot get our IP address."
		return False
	public_address = rem_msg
	rem_msg = ''
	print "Our public IP address is ", public_address
	sleep(5)
	#join to the collector
	sck2.sendto('join',collector)
	print "Next we will join the system and get a list of possible aggregators."
	try:
		rem_msg, rem_addr = sck2.recvfrom(4096)
	except socket.error:
		print "Collector is not listening on this port right now."
		return False
	except socket.timeout:
		print "Collector is not responding right now."
		return False

	#print "received: ", rem_msg
	if rem_msg == 'getl':
		sck2.sendto('setl',collector)
		#print "sent setl"
	else:
		print "Received unexpected message from collector."
		return False
	
	try:
		rem_msg, rem_addr = sck2.recvfrom(4096)
	except (socket.timeout, socket.error):
		print "Received unexpected response from collector.  Collector is not listening or took to long to respond."
		return False
		
	if rem_msg[:4] == 'list':
		c = 4	#start processing msg after 'list'
		s = rem_msg[:len(rem_msg)-len(rem_msg)%4]	#cut off any erroneous extra bytes
		while not c / len(s):
			aggs[socket.inet_ntoa(s[c:c+4])] = 0.0
			c += 4
	else:
		print "Received unexpected response from collector, since we didn't receive the aggregator list message."
		return False
	
	#print "Aggregator List from Collector: ", aggs.keys()
	sleep(5)
	#collect latency times, pick best
	if len(aggs) == 0:	
		print "This is a bad list."
		return False
	elif len(aggs) == 1 and aggs.keys()[0] in collector[0]: #got a list of only the collector
		print "We were selected to forward data straight to the collector. This is great!"
		next_aggregator = collector
	#elif len(aggs) == 1: #got one aggregator
		#next_aggregator = (aggs.keys()[0], 9999)
	else: #got a list of aggregators
		if len(aggs) == 1:
			print "We only got one aggregator.  Let's see if it is listening."
		else:
			print "Testing latencies with potential next-hop aggregators."
		rem_msg = ''
		for i in aggs:
			sck2.sendto('getl', (i,9999))
			aggs[i] = time()
		while 1:
			try:
				rem_msg, rem_addr = sck2.recvfrom(4096)
				if rem_msg == 'setl':
					if rem_addr[0] in aggs:
						aggs[rem_addr[0]] = time() - aggs[rem_addr[0]]
			except socket.timeout:
				break
			except socket.error:
				pass
		lowest = 5.0
		lowest_agg = None
		for i in aggs:
			if aggs[i] < lowest:
				lowest_agg = i
				lowest = aggs[i]
		if lowest_agg != None:
			#print "List with latencies: ", aggs.items()
			next_aggregator = (lowest_agg,9999)
			print "We selected the next aggregator as: ", next_aggregator[0]
		else:
			if len(aggs) == 1:
				print "This aggregator did not work out."
			else:
				print "None of the aggregators from the list worked out."
			return False
	sleep(5)
	print "\nSending aggregation request to collector to see if we can aggregate for others."
	sleep(5)
	sck2.sendto('aggt', collector)
	sleep(1)
	sck.settimeout(0.0)
	while 1:
		try:
			rem_msg, rem_addr = sck.recvfrom(4096)
		except (socket.timeout, socket.error):
			print "No response from collector.  UDP port 9999 may not be open.\n" \
					" - You might look into this if you want this to work.  Did you configure your router and computer's firewall settings to allow this?\n" \
					" - This is not a critical error.  We can forward our data to the next-hop aggregator, but we can't forward data for others."
			break
		else:
			if rem_msg == 'open':
				if rem_addr[0] == collector[0]:
					print "Got open message from collector. we should be able to aggregate data for others!" \
							"The collector may send them our way when they join the aggregation system."
					should_be_aggregator = True
					sck.sendto('aggt', rem_addr)	#won't guarantee we join, but hopefully
					break
		
	#change to non-blocking
	sck.settimeout(0.04) # 40 ms wait, check 25 times per second 
	
	if child_aggs:
		if not should_be_aggregator:
			inform_lost ()
		else:
			for i in child_aggs:
				sck.sendto('chld' + socket.inet_aton(i), collector)
			
	sleep(1) #removed to speed up start time
	print "\nSetup complete!  Let's start sending data."
	return True

def do_setup ():
	count = 0
	while ( setup() != True ):
		count += 1
		print "Setup failed.  Sleeping for ", count, "sec., then we will try again.\n"
		sleep(count)

do_setup ()
print "\nThere may not be much output from here, but leave the program running.\nIf you want to close the program, press Control+c.\n"	
		


#vars for while loop

current_msg = ''
send_msg_interval = randint (101, 1000) / 1000.0
send_interval = send_msg_interval/10.0 # 0.1
check_interval = send_msg_interval*300.0 # 300.0
sent_test = False
t3 = t2 = t1 = time()
# data send and aggregation loop
while 1:
	rem_msg = ''
	rem_addr = ()
	try:
		rem_msg, rem_addr = sck.recvfrom(4096)
	except socket.timeout:
			t = time()
			#send checks
			if t - t1 > send_msg_interval:
				if t2:	#if t2 timer is set, then just reset t1 timer
					t1 = t
				else:	#else set t2 timer, and reset t1 timer
					t2 = t1 = t
				current_msg += socket.inet_aton(public_address)
				#sck.sendto (current_msg, next_aggregator)  #commented out since we want to send on send interval
				#current_msg = ''
				sent_test = False	#reset sent test every one second
			elif t2:
				if t - t2 > send_interval:
					t2 = False #unset t2
					if current_msg:	#shouldn't have to check, but am anyway
						sck.sendto (current_msg, next_aggregator)
						current_msg = ''
			if t - t3 > check_interval:
				t3 = t
				sck.sendto ('test', collector)
				sent_test = True
	except socket.error:
		print "Next hop aggregator is not listening anymore.\nRestarting setup."
		if not setup():
			inform_lost ()
			do_setup ()
		sent_test = False
		t3 = t2 = t1 = time()
		current_msg = ''
		
	else:
		#somebody sent us a nope (meaning, our data wont get to aggregator/collector)
		if rem_msg == 'nope':
				if rem_addr[0] == collector[0]:
					print "Received message from collector indicating the collector wants us to reconnect.\nRestarting setup."
					if not setup():
						#inform child aggs that you are not able to send
						inform_lost ()
						do_setup ()
					sent_test = False	# re initialize
					t3 = t2 = t1 = time()
					current_msg = '' #reset message
				elif rem_addr[0] == next_aggregator[0]:
					print "Received message from the next hop aggregator indicating it may have gone down.\nRestarting setup."
					if not setup():
						#inform child aggs that you are not able to send
						inform_lost ()
						do_setup ()
					t3 = t2 = t1 = time() # reset time
						
		#somebody is checking latency with us			
		elif rem_msg == 'getl':
			print "Somebody is checking latency with us to see if we are a good candidate."
			sck.sendto ('setl', rem_addr)
			
		
		#we received aggregation data
		else:
			current_msg += rem_msg
			t = time()
			if not t2:	#if t2 timer is not set, set it
				t2 = t
			#send checks
			if t - t1 > send_msg_interval:
				if t2:	#if t2 timer is set, then just reset t1 timer
					t1 = t
				else:	#else set t2 timer, and reset t1 timer
					t2 = t1 = t
				current_msg += socket.inet_aton(public_address)
				#sck.sendto (current_msg, next_aggregator)  #commented out since we want to send on send interval
				#current_msg = ''
			elif t2:
				if t - t2 > send_interval:
					t2 = False
					if current_msg:	#shouldn't have to check, but am anyway
						sck.sendto (current_msg, next_aggregator)
						current_msg = ''
			if t - t3 > check_interval:
				t3 = t
				sck.sendto ('test', collector)
			#other check
			if (rem_addr): 
				if (rem_addr not in child_aggs):
					child_aggs.append(rem_addr)
					print "Adding child aggregator since we received data from it.\nChild aggregator address is: ", rem_addr[0]
					sck.sendto('chld' + socket.inet_aton(rem_addr[0]), collector)
			

	

