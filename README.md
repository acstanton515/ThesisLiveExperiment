ThesisLiveExperiment
====================

I am working on a live experiment for my thesis research that will demonstrate my data aggregation framework working over the Internet.  Looking for anyone to run these programs.

Please, please, please participate by downloading the program and running it on your computer. I need your help to make the experiment work!!! 

Data aggregation is a broad term which in my work can be described as a method to reduce or simplify the amount of data being received by a collection device while the data is traversing through a network or networks. Any part of the data is considered whether it is payload or headers carrying the payload. Typically, data aggregation is used in many-to-one communication paradigms where many devices are all sending data to a single device, called the collector.

For an Internet demonstration, I have setup the following data aggregation system:

- You will download a program that you can run on a Windows computer or Linux computer.
- Your client is called an aggregator and participates in generating data and sending it towards the collector via a next-hop aggregator or possibly directly to the collector
- Your aggregator may also be the next-hop aggregator for other nodes and so would forward data from others towards your next hop as well
- In this application, the data being sent is only your public IP address, which you retrieve from an IP lookup service
- This data will be sent at a random interval between 100 milliseconds and 1 second
- The collector is a server of mine at home running on a Raspberry Pi microprocessor board.
- My collector will gather statistics about the number of packets received vs the number of IP address messages collected, and other statistics like how many control messages were received.
- The collector will generate hourly reports of participants, and using those reports I can use the IP address to do a lookup on the IP address' geolocation and generate some nice graphs of user participation.

See my current data aggregation maps at:

https://mapsengine.google.com/map/edit?mid=zRpKPAmWKca8.k1Tk1jn81byA



The programs were written in Python and I converted the script into an executable file for Windows and C code for Linux so that the executable could be built on your Linux system. See the latest posts for instructions for accessing the aggregator program. If you are interested in seeing the Python "source code", please message me.



Aggregator v1.0.0 Linux Distribution 
--------------------

#####Instructions:
Run the following commands once you have the compressed file on your computer.

	tar -zxvf <file name>
	cd dist
	make
	./aggregator
  
Control + c to exit. It will run forever...

######If you want to run it in the background:

	./aggregator &

######If you want it to run at startup of your computer, then add the following line to your user's crontab file:

	@reboot /path/to/aggregator &

To access your crontab file run the following command:

	crontab -e



Aggregator v1.0.0 Windows Distribution 
--------------------

#####Instructions:
Running the application can be done through Windows Explorer once you have the file downloaded to your computer.

	1. Extract the zip file to another folder
	2. Double click on the aggregator application to run the program

######To run the program automatically whenever you log in, follow the instructions at this site:

http://windows.microsoft.com/en-us/windows-vista/run-a-program-automatically-when-windows-starts

It is a command line program, so it should open up a command prompt window.



Would you like an Android app version?
--------------------

I have identified a possible tool to turn my Python code into an Android App using Kivy, but I have not had time as of yet to start developing the GUI component needed to run an app. If you are interested in this please let me know.



How to use the program:
--------------------

####Open Port on your Router/Firewall

In order for your aggregator client to be able to forward data for other aggregators, it will need to behave like a server. If you run this application at home or work or in most public settings, then you will likely not by default be able to be reachable from Internet. If you run it at home, you can change the settings on your home router to open up the port necessary to enable this functionality.

You will need to forward UDP port 9999 to your computer's address.

Inbound:
	UDP/9999 - Receive to Forward
	Outbound:
	UDP/9999 - Send
	UDP/14001 - Get public IP


#####Example outputs when port is not open:

	dmin@box$ ./aggregator
	socket timeout: 5.0
	My Public IP: 54.215.246.142
	sent join
	received: getl
	sent setl
	list: ['23.23.205.15']
	got open msg from collector, should be an aggregator


#####Example outputs when port is open:

	admin@box$ ./aggregator
	socket timeout: 5.0
	My Public IP: 54.215.246.142
	sent join
	received: getl
	sent setl
	list: ['23.23.205.15']
	no response from collector, my port may not be open

####Program Outputs

At this time the program run on a Command Line Interface and just outputs initial setup messages and occassional other control messages.

Right now, the outputs from the program on the command line are not that interesting. You may see:

"somebody is checking latency with us" - this means another node is checking how much latency is between it and you to see if you are a good candidate for being the next-hop aggregator for that node.

"add child due to msg xxxx ('54.229.219.118', 9999)" - this means the node started sending data to you, so you added it to your aggregator list

If the collector is not available, which would likely be my fault, then you will see the program keep trying while adding one second to the back-off period each time.

####Privacy and Protection

The only data sent out by this application is your IP address which you learn through talking with my collector anyway.

There won't be any association between your IP address and any other information about you.
