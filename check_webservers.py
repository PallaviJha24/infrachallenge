#!/usr/bin/env python3
#to run: /usr/lib/nagios/plugins/check_webservers.py
import sys
import requests

#Read server IPs from a file.
with open("/etc/nagios4/conf.d/webservers.txt", "r") as file:
    servers = file.readlines()

#Remove leading/trailing white space
servers = [server.strip() for server in servers]

#Initialize failure counters.
offline_servers = []
for server in servers:
    try:
        response = requests.get(f"http://{server}")
        if response.status_code != 200:
            offline_servers.append(server)
    except requests.exceptions.RequestException:
        offline_servers.append(server)

#Nagios return codes:
#0 = OK, 1 = Warning, 2 = Critical
if len(offline_servers) == 0:
    print("OK: all servers are online")
    sys.exit(0)
elif len(offline_servers)== len(servers):
    print(f"CRITICAL: All servers are offline: {', '.join(offline_servers)}")
    sys.exit(2)
else:
    print(f"WARNING: Servers offline: { ', '.join(offline_servers)}")
    sys.exit(1)