# FindHostname

## Introduction

Find all hostnames in given folder and checks (with recursive dig function) which are in perimeter.

**First**, you should populate a folder with text files containing hostnames. The script identifies all hostnames which presents in files with one regular expression, `sort -u` the list and tries to filter the noise in order to reduce the size of initial input. If you have no idea for populate the initial list, you can add:

 * Nessus xml output,
 * Maltego hostname list,
 * Sublist3r, theHarvester results exports,
 * Burp "site map" txt export,
 * DNS brute force/ Zone transfert,
 * Any export of tools finding hostnames from IP (ex: bing search IP:"X.X.X.X"),
 * Etc...
 
**Second**, populate a txt file with your pentest scope (IP, IP/32, network/cidr).

**Then**, this tool finds those of which the dig command returns an IP belonging to the perimeter file. No more of blah blah, a good schema is better:

![](https://user-images.githubusercontent.com/15103453/28667021-f7ac7750-72c9-11e7-883b-aec1cff4e778.png)

The script resolves and keeps, in the final result, all discovered CNAMEs and all IPs associated with one DNS name. The output is in `nessus` target format:` hostname / vhost [IP] `.

## Installation, dependencies and requirements

### Installation

    git clone https://github.com/jtof-fap/verifHostname.git

### Python version

This script currently supports Python 2 and Python 3.

### Dependencies

verifHostname.py depends on the `docopt`, and `netaddr` python modules :

    # pip install -r requirements.txt

### Requirements

This script need the following requirements to run:

 * On Linux : dig command (`# apt-get install dnsutils`)
 * On Windows : require dig.exe on the same folder and bind libs in system32

## Command line -h (RTFM) ##

#### Arguments: ####

    FOLDER_OR_FILE           File or Folder which gathers the text files containing hostnames.
	PERIMETER_FILE           Perimeter file 1 element/line (IP, IP/32, network/cidr).
	-t, --thread = <num>     Thread number (default (10)).
	-s, --server = <X.X.X.X> DNS Server, prefer robust for multithreading (default (8.8.8.8)).

#### Options: ####

	-h, --help       Print Help
	-v, --version    Print Version
	-d, --debug      Print Debug

#### Usage: ####

	verifHostname.py FOLDER_OR_FILE PERIMETER_FILE
	verifHostname.py FOLDER_OR_FILE PERIMETER_FILE -d
	verifHostname.py FOLDER_OR_FILE PERIMETER_FILE -t xx
	verifHostname.py FOLDER_OR_FILE PERIMETER_FILE -s X.X.X.X
	verifHostname.py FOLDER_OR_FILE PERIMETER_FILE [-d] [-t 5] [-s 8.8.4.4]

## Example usage

#### Inputs: ####

    # cat targets.txt
    www.twitter.com
    https://fiber.google.com/
    /www.google.com 08237
    mail.google.com
    maps.google.com
    yahoo.fr
    testfile.php
    testline
    google.com
    <host>gsuite.google.com/</host>
    <img src="https://store.google.com/">
    firebase.google.com

    # cat perimeter.txt
	172.217.17.0/24
	216.58.204.96/29
	216.58.204.142/32
	216.58.64/29

#### Program: ####

    # python3 verifHostname.py targets.txt perimeter.txt
    INFO > Thread number : 10
	INFO > Check that hostname present in file or folder 'targets.txt' be part of perimeter given in 'perimeter.txt' file
	INFO > Search hostname in 'targets.txt'
	INFO > Program check 10 hostname
	fiber.google.com[216.58.204.142]
	firebase.google.com[216.58.204.142]
	google.com[216.58.204.142]
	gsuite.google.com[216.58.204.142]
	maps.google.com[216.58.204.142]
	store.google.com[216.58.204.142]
	www.google.com[216.58.204.100]
	www3.l.google.com[216.58.204.142]
	INFO > End process.

#### Under the wood / Debug Trace: ####

    # python3 verifHostname.py targets.txt perimeter.txt -d
	INFO > Thread number : 10
	DEBUG > Command line argument :
	  #>FILE OR FOLDER : 'targets.txt'
	  #>PERIMETER : '/tmp/perimeter.txt'
	  #>CUSTOM DNS SERVER : 8.8.8.8
	  #>THREAD NUMBER : 10
	INFO > Check that hostname present in file or folder 'targets.txt' be part of perimeter given in 'perimeter.txt' file
	DEBUG > Perimeter : [['172.217.17.0/24'], ['216.58.204.96/29'], ['216.58.204.142/32'], ['216.58.64/29']]
	DEBUG > Files in folder 'targets.txt' : ['targets.txt']
	INFO > Search hostname in 'targets.txt'
	DEBUG > Hostname list : {'fiber.google.com', 'yahoo.fr', 'google.com', 'firebase.google.com', 'store.google.com', 'www.google.com', 'gsuite.google.com', 'mail.google.com', 'www.twitter.com', 'maps.google.com'}
	INFO > Program check 10 hostname
	DEBUG > dig fiber.google.com +short
	DEBUG > dig yahoo.fr +short
	DEBUG > dig google.com +short
	DEBUG > dig firebase.google.com +short
	DEBUG > dig store.google.com +short
	DEBUG > dig www.google.com +short
	DEBUG > dig gsuite.google.com +short
	DEBUG > dig mail.google.com +short
	DEBUG > dig www.twitter.com +short
	DEBUG > dig maps.google.com +short
	DEBUG > yahoo.fr match 77.238.184.24 but it is not on perimeter... next...
	DEBUG > yahoo.fr match 98.137.236.24 but it is not on perimeter... next...
	DEBUG > yahoo.fr match 106.10.212.24 but it is not on perimeter... next...
	DEBUG > yahoo.fr match 124.108.105.24 but it is not on perimeter... next...
	DEBUG > yahoo.fr match 74.6.50.24 but it is not on perimeter... next...
	DEBUG > CNAME Found for fiber.google.com : www3.l.google.com.
	DEBUG > dig www3.l.google.com. +short
	DEBUG > MATCH SINGLE: www.google.com match 216.58.204.100
	DEBUG > CNAME Found for www.twitter.com : twitter.com.
	DEBUG > MATCH SINGLE: google.com match 216.58.204.142
	DEBUG > CNAME Found for gsuite.google.com : www3.l.google.com.
	DEBUG > dig www3.l.google.com. +short
	DEBUG > CNAME Found for firebase.google.com : www3.l.google.com.
	DEBUG > dig www3.l.google.com. +short
	DEBUG > dig twitter.com. +short
	DEBUG > MATCH SINGLE: maps.google.com match 216.58.204.142
	DEBUG > CNAME Found for mail.google.com : googlemail.l.google.com.
	DEBUG > dig googlemail.l.google.com. +short
	DEBUG > MATCH SINGLE: store.google.com match 216.58.204.142
	DEBUG > MATCH CNAME Recursive call : CNAME fiber.google.com match IP : 216.58.204.142
	DEBUG > MATCH CNAME Recursive call : CNAME www3.l.google.com. match IP : 216.58.204.142
	DEBUG > MATCH CNAME Recursive call : CNAME gsuite.google.com match IP : 216.58.204.142
	DEBUG > MATCH CNAME Recursive call : CNAME www3.l.google.com. match IP : 216.58.204.142
	DEBUG > googlemail.l.google.com. match 216.58.204.133 but it is not in perimeter... next...
	DEBUG > mail.google.com match 216.58.204.133 but it is not in perimeter... next...
	DEBUG > twitter.com. match 104.244.42.129 but it is not in perimeter... next...
	DEBUG > MATCH CNAME Recursive call : CNAME firebase.google.com match IP : 216.58.204.142
	DEBUG > twitter.com. match 104.244.42.1 but it is not in perimeter... next...
	DEBUG > MATCH CNAME Recursive call : CNAME www3.l.google.com. match IP : 216.58.204.142
	DEBUG > www.twitter.com match 104.244.42.65 but it is not in perimeter... next...
	DEBUG > www.twitter.com match 104.244.42.1 but it is not in perimeter... next...
	fiber.google.com[216.58.204.142]
	firebase.google.com[216.58.204.142]
	google.com[216.58.204.142]
	gsuite.google.com[216.58.204.142]
	maps.google.com[216.58.204.142]
	store.google.com[216.58.204.142]
	www.google.com[216.58.204.100]
	www3.l.google.com[216.58.204.142]
	INFO > End process.

## Tips and tricks

If you just wanna check which hostnames are valid (with CNAME resolve), put in the `perimeter` file:

    0.0.0.0/0

## License

`verifHostname` is licensed under the GNU GPL license(Version 3). Take a look at the [LICENSE](LICENSE) for more information.

## Version

Current version is `1.0`