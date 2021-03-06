#!/usr/bin/env python

#-------------------------------------------------------------------------
# Creation Date: Thu May 2020                                             
#
# @ Author: Patrick Stel                                                  
# @ Purpose: Script to check if NAS is powered on, turn off if it's idle. 
#            Script is running from Raspberry PI with Sonarr installed.
#-------------------------------------------------------------------------

import paramiko
import requests
import datetime
import os
import holidays

# General Parameters
nzbGet_active = "yes"
transmission_active = "yes"
officehours_active = "no"
PlexPlayingStatus = "no"
searchString = "Download queue is empty."
searchPlaying = "state=\"playing\""
lookup_MobileDeviceSwitch = '"Status" : "Off",'
startOfficeHours = 7
endOfficeHours = 17
nl_holidays = holidays.NL()
DomoticzIP = "192.168.0.125:8080"

# SSH Credentials (not secure)
host_ip = '192.168.0.0' # Host ip where the download client is running
ssh_username = '********' # SSH Username for host
ssh_password = '********' # SSH Password for host

count_transmission_lines=0
dateToday = datetime.date.today()
currentDateTime = datetime.datetime.now()
dayoftheweek = datetime.datetime.today().weekday() # 0 = monday, 6 = sunday

# Check if NAS is actually running (ping)
response = os.system("ping -c 1 " + host_ip)

if response == 0:
    if dayoftheweek < 5:
        if dateToday not in nl_holidays:
            # Transmission Check
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host_ip, username=ssh_username, password=ssh_password)

            #change admin:admin to what ever your Transmission credentials are.
            stdin, stdout, stderr = client.exec_command('cd /usr/local/transmission/bin/ ;./transmission-remote -n \'admin:admin\' -l')

            for line in stdout:
                count_transmission_lines=count_transmission_lines+1

            client.close()

            if count_transmission_lines == 2:
                transmission_active = "no"

            #NZBGet Check
            link_nzbget = "http://" + host_ip + ":6789/"
            webpage_nzb = requests.get(link_nzbget)

            check_string = searchString in webpage_nzb.text
            if check_string:
                nzbGet_active = "no"

            if currentDateTime.hour > startOfficeHours and currentDateTime.hour < endOfficeHours:
                officehours_active = "yes"

            # Check if Plex is playing something, holiday or dayoff
            link_plex = "http://" + host_ip + ":32400/status/sessions"
            webpage_plex = requests.get(link_plex)

            check_string_plex = searchPlaying in webpage_plex.text
            if check_string_plex:
                PlexPlayingStatus = "yes"

            if transmission_active == "no" and nzbGet_active == "no" and officehours_active == "yes" and PlexPlayingStatus == "no":
                getMobileDeviceSwitch = requests.get("http://" + DomoticzIP + "/json.htm?type=command&param=getlightswitches&idx=22") #check IDXs
                if lookup_MobileDeviceSwitch in getMobileDeviceSwitch.text:
                    # Shutdown the NAS -> NOT COMPLETLY WORKING...
                    client_shutdown = paramiko.SSHClient()
                    client_shutdown.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client_shutdown.connect(host_ip, username=ssh_username, password=ssh_password)

                    stdin, stdout, stderr = client_shutdown.exec_command('sudo shutdown -h now')

                    client_shutdown.close()
