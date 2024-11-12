# infrachallenge
Overview
This guide covers the setup of a miniature environment on four Ubuntu 20.04 servers with the following components.
1. Two web servers: Serve distinct content("a" and "b").
2. Load Balancer: Nginx configured with sticky sessions and IP forwarding.
3. Nagios Monitoring: Monitors the servers and load balancer with a custom check.
4. User access and security: Configure a restricted SSH setup and firewall.

Setup Overview:
I have 4 servers configured with the following IPs:
* Web Server1: 52.42.89.70
* Web Server2: 34.222.236.244
* Load Balancer: 35.93.225.129
* Nagios Monitoring Server: 35.94.238.209

Each server has specific roles and configuration documented in the following sections.



1.Web Server Configuration:
Step 1.1: Installing Apache2 and setting up Index Pages.

	On Web Server1: 52.42.89.70
	sudo apt update
	sudo apt install -y apache2

	#create index.html to serve "a".
	echo "a" | sudo tee /var/www/html/index.html 


	Web Server2: 34.222.236.244
	sudo apt update
	sudo apt install -y apache2

	#create index.html to serve "b".
	echo "b" | sudo tee /var/www/html/index.html

Challenges and Design choices:
* Web server selection: Apache2 was chosen for simplicity. Also, it is reliable and widely used web server.
* Served simple "a" and "b" text files to easily distinguish between the two servers.



2.Load Balancer setup:
Step 2.1: Install nginx as Load Balancer
* We'll use Nginx as the load balancer on the third server(35.93.225.129).

Step 2.2: On 35.93.225.129:
	sudo apt update
	sudo apt install -y nginx

Step 2.3: Edit file "/etc/nginx/nginx.conf" to configure upstream configuration and "/etc/nginx/sites-available/default" to include the server block.
	#Example is present in repo.

Step 2.4: Also, you can test and validate NGINX configuration with below command.
	sudo nginx -t

Step2.5: If the test passes, reload NGINX to apply the changes:
	sudo systemctl reload nginx

Challenges and Design choices:
* Load Balancing Schema: Chose round-robin with sticky sessions to ensure subsequent requests from the same client are directed to the same web server.
* Sticky Sessions: Ensured Nginx maintains session persistence so clients are routed to the same web server unless it's down.
* X-Real-IP Header: Ensured the original IP is passed along to the web servers for logging or any IP-based configuration.



3. Nagios Setup on 4th Server:
Step 3.1: Install Nagios core on the 4th server(35.94.238.209).
	sudo apt update
	sudo apt install -y nagios4 nagios-plugins-basic


Step 3.2: configure Nagios to Monitor the Servers.
	Create a configuration file to monitor the web servers and the load balancer.
		sudo vi /etc/nagios4/conf.d/webservers.cfg
		#Refer repo for config.


Step 3.3: Reload Nagios.
	sudo systemctl restart nagios4


Challenges and Design choices:
* Used Nagios Core for simplicity and ease of use in monitoring the servers.
* Ensured monitoring of the web servers and load balancer to detect service issues.


4.Custom Nagios Check(Python Script)
Created a custom Nagios plugin to monitor the web servers by reading from a file and checking their status.

Step 4.1: Create a Python Nagios Plugin.
Create the script to read list of web servers from a file and check if they are online.
sudo vi /usr/lib/nagios/plugins/check_webservers.py
#Refer script from Repo.


Step 4.2: Make the script executable.
sudo chmod +x /usr/lib/nagios/plugins/check_webservers.py

Step 4.3: Add web servers to a file.
sudo vi /etc/nagios4/conf.d/webservers.txt


Add IP of the web server.
52.42.89.70
34.222.236.244


Step 4.4: Test the script.
Run the python script to test its functionality.
/usr/lib/nagios/plugins/check_webservers.py

Challenges and Design choices:
* Custom Nagios check: Wrote a Python script using the `request` library to ping the web servers. The script checks for the HTTP status and exits with appropriate Nagios return codes.
* File-based configuration: The script reads web server IPs from a file to allow easy updates withoout modyfying the script.



5. User Setup:
Step 5.1: Create user 'expensify'.
On each server:
sudo useradd -m expensify
sudo passwd expensify

Step 5.2: Grant Sudo access
sudo usermod -aG sudo expensify

Step 5.3: Install shared public keys for authentication.
sudo mkdir /home/expensify/.ssh
sudo vi /home/expensify/.ssh/authorized_keys
sudo chown -R expensify:expensify /home/expensify/.ssh

Step 5.4:Validate user.
ubuntu@ip-172-30-0-79:~$ sudo su - expensify
$whoami
expensify

Challenges and Design choices:
* Needed to format shared keys file.


6. Network Lockdown:
Step 6.1: Configure SSH and Firewall rules on Load balancer(35.93.225.129).
	1. Expose only the Load balancer(35.93.225.129) to the public(port 80,443)
		sudo ufw allow 80
		sudo ufw allow 443
	2. Allow ssh from Anywhere(for management).
		sudo ufw allow 22
	3. Deny all other incoming connections.
		sudo ufw default deny incoming
		sudo ufw enable

Step 6.2: On the web servers and Nagios Server(Internal Access only).
	1. Deny Public access to All ports(on each web server and the Nagios server).
		sudo ufw default deny incoming
		sudo ufw allow from <load_balancer_ip> to any port 80

	2. Allow SSH access only from Load Balancer.
		sudo ufw allow from <load_balancer_ip> to any port 22

	3. Enable the firewall.
		sudo ufw enable


Challenges and Design choices:
* Load balancer: Public HTTP/HTTPS(port 80/443) and public ssh (port 22).
* Web serverS: HTTP(port 80) accessible only from the load balancer; SSH(port 80)
* Nagios Server: SSH(port 22) accessible only from the load balancer.
* Security: Restricted SSH access to a single server.
* Firewall Configuration: Configured UFW for strict control over incoming connections.




Conclusion:
This setup ensures high availability with load balacing , robust monitoring, and secure access controls.

Referances:
https://ubuntu.com/server/docs/firewalls

