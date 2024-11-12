# infrachallenge
Overview
This guide covers the setup of a miniature environment on four Ubuntu 20.04 servers with the following components.
1. Two web servers: Serve distinct content("a" and "b").
2. Load Balancer: Nginx configured with sticky sessions and IP forwarding.
3. Nagios Monitoring: Monitors the servers and load balancers with a custom check.
4. User access and security: Configure a restricted SSH setup and firewall.

Setup Overview:
I have 4 servers configured with the following IPs:
* Web Server1
* Web Server2
* Load Balancer
* Nagios Monitoring Server

Each server has specific roles and configurations, which are documented in the following sections.



1. Web Server Configuration:
	Step 1.1: Install Apache2 and set up Index Pages.
	On Web Server1: 
	
			sudo apt update
			sudo apt install -y apache2
			
			#create index.html to serve "a".
			echo "a" | sudo tee /var/www/html/index.html 
	
	
	On Web Server2:
	
			sudo apt update
			sudo apt install -y apache2
		
			#create index.html to serve "b".
			echo "b" | sudo tee /var/www/html/index.html
	
	Challenges and Design choices:
	* Web server selection: Apache2 was chosen for simplicity. Also, it is a reliable and widely used web server.
	* Served simple "a" and "b" text files to easily distinguish between the servers.



2. Load Balancer setup:
	Step 2.1: Install Nginx as Load Balancer
	* We'll use Nginx as the load balancer on the third server.
	
	Step 2.2: On Load Balancer:
	
		sudo apt update
		sudo apt install -y nginx
	
	Step 2.3: Edit file "/etc/nginx/nginx.conf" to configure the upstream configuration.
			
	  		upstream web_servers {
			    ip_hash;
			    server <ip_web_Server1>;  # Web Server 1
			    server <ip_web_Server2>;  # Web Server 2
			}
	
	
	
	And "/etc/nginx/sites-available/default" to include the server block.
	
		server {
		        listen 80;
		        server_name _;
		        location / {
		            proxy_pass http://web_servers;
		            proxy_set_header X-Real-IP $remote_addr;
		            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		        }
		
		        # Port range 60000-65000 forwarding to web servers on port 80
		        server {
		            listen 60000-65000;
		            proxy_pass http://web_servers;
		        }
	    	}
	
	Step 2.4: Also, you can test and validate NGINX configuration with the below command.
	
		sudo nginx -t
	
	Step2.5: If the test passes, reload NGINX to apply the changes:
	
		sudo systemctl reload nginx
	
	Challenges and Design choices:
	* Load Balancing Schema: Chose a round-robin with sticky sessions to ensure subsequent requests from the same client are directed to the same web server.
	* Sticky Sessions: Ensure Nginx maintains session persistence so clients are routed to the same web server unless it's down.
	* X-Real-IP Header: Ensured the original IP is passed along to the web servers for logging or any IP-based configuration.
	* However, due to port range 60000-65000 on the load balancer, as existing worker connection was not enough for listening sockets and because of that resource limit was hit. Overcome this issue by modifying the system config.
	  Err: nginx: [emerg] 768 worker_connections are not enough for 5002 listening sockets
	In case you also hit the similar issue, you can proceed with below steps(Keep in mind other OS performance tuning might be required per your setup).
	
	* Increase the worker_connection value(look for worker_connection directive inside event block).
	
			sudo vi /etc/nginx/nginx.conf
	* Increasing worker_rlimit_nofile is optional.
	
	   		worker_rlimit_nofile 100000;
	* Test the configuration(always check the nginx config after any change in case the error varies).
	
	   		sudo nginx -t
	* Restart nginx if test passes without Error.
	
	   		sudo systemctl restart nginx
	* Also, keep in mind to check the system limit, if your OS allows for increased number of file descriptor.
	
	   		ulimit -n
	* If necessary, increase the limits by editing /etc/security/limits.conf to allow for more open files:
	   	
	    		*          soft    nofile  100000
			*          hard    nofile  100000



3. Nagios Setup on 4th Server:
	Step 3.1: Install the Nagios core on the 4th server.
	
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
  		<ip_web_Server1>
		<ip_web_Server2>
	
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
	Step 6.1: Configure SSH and Firewall rules on Load balancer.
		1. Expose only the Load balancer to the public(port 80,443)
	 
				sudo ufw allow 80
				sudo ufw allow 443
		3. Allow ssh from Anywhere(for management).
	
				sudo ufw allow 22
		5. Deny all other incoming connections.
	    
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

