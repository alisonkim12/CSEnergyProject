"""pseudo code of checking
for idle status of computer

Alison Kim
2.2.2020
"""
#!/usr/bin/env python3

import argparse
import configparser
import os
import requests
import socket
import subprocess
import time

config = None

def send_to_influx(username, password, status):
    requests.post(
        'http://influx.cs.swarthmore.edu:8086/write?db=SCI240',
        data='sleep_status,host=%s status="%s"' % (socket.gethostname(), status),
        auth=(username, password)
    )

def main():
    parser = argparse.ArgumentParser(description='Put idle hosts to sleep.')
    parser.add_argument('-c', '--config', dest='config', default='idlecheck.ini')
    args = parser.parse_args()

    global config

    config = configparser.ConfigParser()
    config.read(args.config)
    lastsleep = time.time()

    while True:
        policy = config["Policy"].get("policyname")
        if policy == "sleep_userlogin":
            decision = sleep_userlogin()
        elif policy == "sleep_combination":
            decision = sleep_combination()

        if decision == True and (lastsleep + int(config["Policy"].get("timecheck")) < time.time()):
            send_to_influx(config["Influx"].get('username'), config["Influx"].get('password'), 'sleep')

            lowpowermode()

            lastsleep = time.time()
            time.sleep(1) # necessary for network to reconnect?
            send_to_influx(config["Influx"].get('username'), config["Influx"].get('password'), 'wake')

        time.sleep(int(config['Idlestatus'].get('interval')))


def sleep_combination():
        decision = True
        if sleep_userlogin() == True: #if there is no student logged in
            return decision #go to sleep

        solutionlist = getCPUandRunningProcesses()
        for solution in solutionlist:
            cpu,executable = solution #forgot what this does, does it get the lowest cpu from the top five?
        print("this is the CPU:",cpu)
        print("this is the executable:",executable) #executable is sort, where does that come from?

        if executable == config["Parameter"].get('application') and cpu > config["Parameter"].get('cpu'):
             #checking for scenario where computer is running a program
             decision = False #don't go to sleep

        if IsItNightTime() == False and sleep_keyboardactivity() == False:
            decision = False #don't go to sleep

        print("Computer has decided on the decision", decision)
        return decision


def sleep_userlogin():
    #something about getting a boolean variable of whether there is a person logged in
    #next step: subprocess module?
    result = subprocess.run(["who", "-q"], stdout = subprocess.PIPE)
    stringresult = result.stdout.decode("utf-8")
    if "users=0" in stringresult:  #this means that no one should be logged in
    #goal: need to see what happens when no one is logged into the computer. need to use systemd
        print('going through user login policy, returning True, zero users')
        return True
    else:
        print('going through user login policy, returning False, one or more users')
        return False


def lowpowermode():
    try:
        print('Attempt suspend')
        subprocess.run(['sudo', 'systemctl', 'suspend'])
    except Exception as e:
        print(e)

def getCPUandRunningProcesses():
    p1 = subprocess.Popen(["ps", "ax", "-o", "%cpu=,command="], stdout= subprocess.PIPE)
    p2 = subprocess.Popen(["sort", "-r"], stdin=p1.stdout, stdout=subprocess.PIPE)
    #p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    #output = p2.communicate()[0]

    p3 = subprocess.Popen(["head", "-n", "5"],stdin=p2.stdout, stdout=subprocess.PIPE)
    #p2.stdout.close()
    output = p3.communicate()[0]
    stringresult = output.decode("utf-8")
    p1.wait()
    p2.wait()
    linelist = stringresult.splitlines()
    print(linelist)
    solutionlist = []
    for i in range(len(linelist)-1):
        wordlist = linelist[i].split()
        cpu = float(wordlist[0])
        executable = wordlist[1]
        solutionlist.append((cpu, executable))
    print(solutionlist)
    print("returning CPU and executable to sleep combination function")
    return solutionlist
    #call split of string [0], which will be the CPU (convert to float) [1] is the executable

def IsItNightTime():
    result = subprocess.run(["date", "+%H"], stdout = subprocess.PIPE) #just to display timne
    stringresult = result.stdout.decode("utf-8")
    print(stringresult)
    if int(stringresult) >= int(config["Parameter"].get('mintime')) and int(stringresult) <= int(config["Parameter"].get('maxtime')):
        print("night time policy: returning True, it is night time ")
        return True
    else:
        print("night time policy: returning False, it isn't night time ")
        return False


def sleep_keyboardactivity():
    # call the c file
    # eventually giving the keyboard activity in millisecond...set to a int variable called timeidle
    result = subprocess.run(["sudo", "/usr/swat/suspend/system_idle_time"], stdout = subprocess.PIPE)
    stringresult = result.stdout.decode("utf-8")
    print(stringresult)
    mintimeidle = int(stringresult.split()[0])
    if mintimeidle//3600000 > int(config["Parameter"].get('keyboardidletime')):  #diving by 3600000 should give the time in hours
        print("keyboard activity policy: returning True, has been idle for more than min time")
        return True
    else:
        print("keyboard activity policy: returning False, has not been idle for more than min time")
        return False


    #if no keyboard activity for > 3 hours, then lowpowermode()


'''
revisit this?
def sleep_energylevel():
    #import updated data on the energy levels of the Computer and convert into an int

    energylevel = int(config["Idlecheck"]["energylevel"])
    if energylevel < 50 and energylevel > 40:
        return "low enough"

loginstatus = userlogin()
if loginstatus == False:
    #int(config["Idlecheck"].get("userlogin")) = 0 # 1 or 0 depending on how we find the login info
    #bool(config["Idlestatus"].get("sleep")) = True
    print(" %s is going on low power mode..." % computername)
    lowerpowermode()

elif energylevel() == "low enough":
    bool(config["Idlestatus"].get("sleep")) = True
    print(" %s is going on low power mode..." % computername)
    lowerpowermode()
'''

if __name__ == '__main__':
    main()
