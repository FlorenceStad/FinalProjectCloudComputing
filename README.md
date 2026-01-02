MySQL Cluster with Proxy and Gatekeeper (LOG8415E)
This project implements a distributed MySQL cluster on Amazon EC2. The architecture utilizes the Gatekeeper and Proxy cloud design patterns to separate concerns between security, routing logic, and data storage.

System Architecture
The infrastructure consists of five EC2 instances organized into three tiers:
Gatekeeper (t2.large): The only internet-facing instance. It handles authentication and SQL sanitization.
Proxy / Trusted Host (t2.large): An internal instance that performs read/write separation and load balancing.

Database Cluster (3x t2.micro):
Manager: Handles all WRITE operations and replicates data to workers.
Workers (x2): Handle READ operations to ensure horizontal scalability.

Deployment Instructions
1. Infrastructure Provisioning
Run the automation script to provision the EC2 instances, security groups, and network configurations:

2. Manual Service Setup
Once the instances are running, follow these steps to start the application layers:

A. Database Layer
Ensure MySQL is running with Master-Slave replication configured. The Sakila database must be loaded on all nodes.

B. Proxy Layer
SSH into the Proxy instance.
Navigate to the code directory and install dependencies: pip install flask mysql-connector-python.

Start the Proxy service:
Bash
python3 proxy.py

C. Gatekeeper Layer
SSH into the Gatekeeper instance.
Install dependencies: pip install flask requests.

Start the Gatekeeper service:
Bash
python3 gatekeeper.py

Benchmarking
To evaluate the system, run the benchmarking script from your local machine or a separate test instance:
Bash
python3 benchmarking.py
This script dispatches 1,000 requests per strategy to measure performance across Direct Hit, Random, and Customized routing.

Security Features
Input Validation: The Gatekeeper rejects destructive SQL commands (e.g., DROP, TRUNCATE).
Network Isolation: Security groups are configured so the Database and Proxy layers are not accessible from the public internet.
Authentication: All requests to the Gatekeeper require a valid API key.

Project Structure
finalproject.py: Boto3 script for AWS provisioning.
gatekeeper.py: Flask application for request validation.
proxy.py: Flask application for read/write separation and routing.
benchmarking.py: Performance testing and data collection script.