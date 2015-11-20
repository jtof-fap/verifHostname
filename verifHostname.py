#!/usr/bin/env python3
"""Find all hostnames in given folder and checks (with recursive dig function) which are in perimeter.

First, you should populate a folder with text files containing hostnames. If you have no idea :
 - Nessus xml output, 
 - Maltego hostname list, 
 - TheHarvester export,
 - Burp "site map" txt export,
 - DNS brute force/ Zone transfert,
 - Any export of tools finding hostnames from IP (bing IP:"X.X.X.X"),
 - Etc..

Then, this tool finds those of which the dig command returns an IP belonging to the perimeter file.

Require:
    On linux : dig command
    On Windows : require dig.exe on the same folder and bind libs in system32

Usage:
    verifHostname.py FOLDER TARGETFILE
    verifHostname.py FOLDER TARGETFILE -d
    verifHostname.py FOLDER TARGETFILE -t xx
    verifHostname.py FOLDER TARGETFILE -d -t xx

Arguments:
    FOLDER               Folder which gathers the text files containing hostnames.
    TARGETFILE           Perimeter file 1 element/line (IP, IP/32, network/cidr)
    -t, --thread = <num> Thread number (default (10))

Options:
    -h,--help       Print Help
    -v,--version    Print Version
    -d,--debug      Print Debug

Exemple:
    verifHostname.py /path/folder perimeter.txt
    verifHostname.py /path/folder perimeter.txt -d -t 10
"""

import logging
import glob
import os.path
import sys
import re
import threading
import os
import subprocess
import shlex
from netaddr import *  # pip-3.2 install netaddr
from docopt import docopt
from multiprocessing.dummy import Pool as ThreadPool


logger = logging.getLogger(__name__)


def set_logger(level):
    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter('%(levelname)s > %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class VerifHostname():

    """ Main class """

    def __init__(self, options):
        # Default logger level
        if options["--debug"]:
            set_logger(logging.DEBUG)
        else:
            set_logger(logging.INFO)

        # Platform definition
        if hasattr(sys, 'getwindowsversion'):
            self.__os = "Windows"
        else:
            self.__os = "Linux"

        # Thread number definition
        self.__thread = 10  # default
        if options["--thread"]:
            self.__thread = int(options["--thread"])

        # Variable definition
        self.__counter = 1
        self.__listSize = 0
        self.__currentFile = ""
        self.__perimeter = []
        self.__filelist = []
        self.__hostnameList = []
        self.__filteredHostnameList = []
        self.__finalOutput = []
        self.__finalOutput2 = []
        self.__directoryfile = options["FOLDER"]
        self.__perimeterfile = options["TARGETFILE"]
        self.__matchIP = re.compile(
            "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
        self.__matchHostname = re.compile(
            r"\b((?=[a-z0-9-]{1,63}\.)(xn--)?[a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,63}\b",
            re.DOTALL | re.IGNORECASE | re.MULTILINE)
        self.__filterHostname = re.compile(
            r".*\.?(html|php|avi|mp3|jsp|asp|aspx|php3|php4|php5|nasl|xml|crl|crt|nbin|src|js|css|png|jpeg|gif|swf|"
            r"jpg|pdf|doc|txt|form|html5|htm|craigslist\.org)",
            re.IGNORECASE)
        self.__pool = ThreadPool(self.__thread)
        logger.info("Thread number : %d", self.__thread)

        listHost = []
        outtmp = []

        logger.debug(
            "Command line argument :\nFOLDER : '%s'\nPERIMETER : \'%s', \nTHREAD NUMBER : %d",
            self.__directoryfile,
            self.__perimeterfile,
            self.__thread)

        # Run main program
        self.program()

    def program(self):
        """ Main program start """
        logger.info(
            "Check that hostname present in file or folder '%s' be part of perimeter given in '%s' file\n",
            self.__directoryfile,
            self.__perimeterfile)

        # Get list from perimeter
        self.__perimeter = self.getPerimeter(self.__perimeterfile)
        logger.debug("Perimeter : %s", self.__perimeter)

 	# Get full path list of files presents in given folder (+ subfolders)
        self.__filelist = self.listdirectory(self.__directoryfile)
        logger.debug("File in folder '%s' : %s ", self.__directoryfile, self.__filelist)

        # Get uniq sorted hostname list from files
        self.__hostnameList = self.getRegexpMatchFromFileList(self.__filelist, self.__matchHostname)

        # Filter filename ex: 'xxx.php' in hostname list
        self.__hostnameList = filter(lambda x: not self.__filterHostname.search(x), self.__hostnameList)
        self.__filteredHostnameList = set(self.__hostnameList)
        logger.debug("Hostname list : %s", self.__filteredHostnameList)

        # Starting recursive multithreaded dig command and comparing results with perimeter
	# - CNAME compatibility (dig mail.google.com +short)
	# - Multiple IP addresses from single hostname compatibility (ex: dig A serverfault.com +short)
        self.__finalOutput = self.callDigOnList(self.__filteredHostnameList)

        # Sort -u on final list
        self.__finalOutput2 = sorted(set(self.__finalOutput))
        for line in self.__finalOutput2:
            print(line)

        logger.info("Traitement Termine.")

    def run_command(self, cmd):
        return subprocess.check_output(shlex.split(cmd))

    def callDigOnList(self, hostnameList):
        """Multithreaded command call on a list and return a final filtered list"""
        outtmp = []

        # Run multithreaded method
        logger.info("Program check %d hostname", len(hostnameList))
        results_map = self.__pool.map(self.dig, hostnameList)
        self.__pool.close()
        self.__pool.join()

        # Get & filter results
        for result in results_map:
            for line in result:
                stripoint = re.sub("\.\[", "[", line, re.DOTALL)
                outtmp.append(stripoint)

        return outtmp

    def getRegexpMatchFromFileList(self, fileList, regExp):
        """ Return uniq sorted list of regexp match in file list """
        matchList = []

        # For each file in list
        for file in fileList:
            logger.info("Search hostname in '%s'", file)
            self.__currentFile = open(file, mode="r")

            # Foreach line in file 
            for line in self.__currentFile:
                
                # Add each match to single list
                for match in re.finditer(regExp, line):
                    # FILTER 1 : Strip end point if regExp match dns hostname : 'www.host.tld.'
                    s = match.start()
                    e = match.end()
                    stripPoint = re.sub("\.$", "$", line[s:e], re.DOTALL)

                    # Append
                    matchList.append(stripPoint)  # print(line[s:e])

            # Close file and next
            self.__currentFile.close()

        # Sort -u of matchList
        return (sorted(set(matchList)))

    def dig(self, *args):
        """ Recursive dig function"""
        ipList = []
        cnameList = []
        perimeter = self.__perimeter
        ipREGEXP = self.__matchIP
        hostnameREXEXP = self.__matchHostname

        # Recursive declarations
        urlTocheck = args[0]
        logger.debug("dig %s +short",urlTocheck)

	# If 3 args, recursive call / CNAME list in progress
        if len(args) == 3:
            cnameList = args[2]

        # Command dig +short
        if self.__os == "Windows":
            cmd = "dig.exe " + urlTocheck + " +short @8.8.8.8"
        else:
            cmd = "dig " + urlTocheck + " +short @8.8.8.8"
        ResultDig = self.run_command(cmd)
        digList = ResultDig.decode('utf-8').splitlines()

        # For each line of dig result
        for element in digList:
            # If match IP address
            if re.match(ipREGEXP, element):
                
                # And IP is in perimeter
                if self.isIPinPerimeter(element, perimeter):
                    #logger.debug("Element %s in dig result",element)
                    
                    # Recursive CNAME Case
                    if cnameList:
                        for cname in cnameList:
                            if urlTocheck in cnameList:
                                ipList.append(cname + "[" + element + "]")
                        
                        logger.debug("MATCH CNAME Recursive call : CNAME %s match IP : %s", cname, element)
                        cnameList.append(urlTocheck)
                        # del(cnameList[:])
                    
                    # Normal Case
                    else:
                        ipList.append(urlTocheck + "[" + element + "]")
                        logger.debug("MATCH SINGLE: %s match %s", urlTocheck, element)
                else:
                    logger.debug("%s match %s but it is not on perimeter... next...", urlTocheck, element)

            # Elif hostname match, one or many CNAME are present in results
            elif re.match(hostnameREXEXP, element):

                if urlTocheck not in cnameList:
                    # Add to CNAME list in order to limit the recursive calls.
                    logger.debug("CNAME Found for %s : %s", urlTocheck, element)
                    cnameList.append(urlTocheck)

                    # Recursive call
                    self.dig(element, perimeter, cnameList)

                elif urlTocheck in cnameList:
                    logger.debug("Recursive call DO NOTHING : %s already processed for %s", element, urlTocheck)
                    # del(cnameList[:])
                    # cnameList.remove(urlTocheck)

        return ipList

    def getPerimeter(self, filename):
        perimeter = []
        file = open(filename, "r")
        for line in file:
            perimeter.append(line.splitlines())
        file.close()

        return perimeter

    def listdirectory(self, path):
        filelist = []
        l = glob.glob(path + '/*')
        for i in l:
            if os.path.isdir(i):
                filelist.extend(self.listdirectory(i))
            else:
                filelist.append(i)

        return filelist

    def isIPinPerimeter(self, ip, permimeterList):
        for network in permimeterList:
            network = network[0]
            if not re.search("/", network):
                if IPAddress(network).is_unicast() and (IPAddress(ip) == IPAddress(network)):
                    return True
            elif re.search("/32", network):
                netip = re.sub("/32", "", network)
                if IPAddress(netip).is_unicast() and (IPAddress(ip) == IPAddress(netip)):
                    return True
            elif IPAddress(ip) in IPNetwork(network):
                return True
        return False

    def ipFromRangeAnyFormat(line):
        iplist = []
        if not re.search("/", line):
            if IPAddress(line).is_unicast():  # and not ip.is_private()
                #print("IP unique : "+str(line))
                iplist.append(line)
        elif re.search("/32", line):
            #print("IP unique : "+line.strip('/32'))
            iplist.append(re.sub("/32", "", line))
        else:
            for ipaddr in IPNetwork(line).iter_hosts():
                #print("network : "+str(ipaddr))
                iplist.append(ipaddr)


if __name__ == "__main__":
    """ Main function """

    arguments = docopt(__doc__, version='0.9')

    # Call main class
    VerifHostname(arguments)
