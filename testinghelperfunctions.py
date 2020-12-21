import argparse
import configparser
import os
import requests
import socket
import subprocess
import time

def main():
    p1 = subprocess.Popen(["ps", "ax", "-o", "%cpu=,command="], stdout= subprocess.PIPE)
    p2 = subprocess.Popen(["sort", "-r"], stdin=p1.stdout, stdout=subprocess.PIPE)
    #p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    #output = p2.communicate()[0]

    p3 = subprocess.Popen(["head", "-n", "5"],stdin=p2.stdout, stdout=subprocess.PIPE)
    #p2.stdout.close()
    output = p3.communicate()[0]
    stringresult = output.decode("utf-8")
    print(stringresult)
    p1.wait()
    p2.wait()
    linelist = stringresult.splitlines()
    print("this is the linelist")
    print(linelist)
    for i in range(len(linelist)-1):
        wordlist = linelist[i].split()
        cpu = float(wordlist[0])
        executable = wordlist[1]
        print("this is the cpu and executables for each line")
        print(cpu)
        print(executable)
        if executable == "terminal" and cpu > 65.0: #checking for scenario where computer is running a program
            print("policy: sleep")
            return True
    return False

main()
