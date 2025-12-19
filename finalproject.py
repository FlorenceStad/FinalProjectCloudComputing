
import os 
import argparse 
import boto3 

def get_keypath(keyname): 
    print("Locating keypair") 
    key_path = os.path.expanduser(f"~/.ssh/{keyname}.pem") 
    
    if not os.path.exists(key_path): 
        raise FileNotFoundError(f"Keypair not found at {key_path}") 
    
    print("Keypair found") 
    return key_path 

def wait_for_instance(instance): 
    print(f"Waiting for {instance.id} to enter running state...") 
    instance.wait_until_running() 
    instance.reload() 
    return instance.public_ip_address, instance.private_ip_address 

def launch_instance(keyname, ec2, sg_id, instance_type, name, userdata=""): 
    instance = ec2.create_instances( 
        ImageId="ami-0bbdd8c17ed981ef9", 
        InstanceType=instance_type, 
        MinCount=1, MaxCount=1, 
        KeyName=keyname, 
        SecurityGroupIds=[sg_id], 
        TagSpecifications=[{ 
            "ResourceType": "instance", "Tags": [{"Key": "Name", "Value": name}] 
            }], 
            UserData=userdata
        )[0] 
    
    print(f"Launched {name} ({instance.id})") 
    public_ip, private_ip = wait_for_instance(instance) 
    
    print(f"{name} PUBLIC IP: {public_ip}") 
    print(f"{name} PRIVATE IP: {private_ip}\n") 
    
    return instance 


def create_sg(ec2): 
    print("Checking security group 'allow-ssh'") 
    
    group_name = "allow-ssh" 
    try: 
        existing = list(ec2.security_groups.filter(GroupNames=[group_name])) 
        if existing: 
            print("Security group already exists.") 
            return existing[0].group_id 
    except Exception: 
        print("Security group not found. Creating new one...") 
        
        vpcs = list(ec2.vpcs.filter(Filters=[{"Name": "isDefault", "Values": ["true"]}])) 
        if not vpcs: 
            raise RuntimeError("No default VPC found. Cannot create SG.") 
        
        vpc_id = vpcs[0].id 
        
        sg = ec2.create_security_group(
            GroupName=group_name,
            Description="Allow SSH, MySQL, Gatekeeper, Proxy",
            VpcId=vpc_id
            )
        
        sg_id = sg.group_id 
        print(f"Created SG with ID: {sg_id}") 
        
        # Ingress rules 
        ec2.meta.client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]},
                {"IpProtocol": "tcp", "FromPort": 3306, "ToPort": 3306, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]},
                {"IpProtocol": "tcp", "FromPort": 8080, "ToPort": 8080, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]},
                {"IpProtocol": "tcp", "FromPort": 8081, "ToPort": 8081, "IpRanges": [{'CidrIp': '0.0.0.0/0'}]},
                    ]
                ) 
        
        print("Ingress rules applied.")
        return sg_id 
    
    
def main(keyname): 
    get_keypath(keyname) 
    ec2 = boto3.resource("ec2", region_name="us-east-1")
    sg_id = create_sg(ec2) 
    
    print("\nStarting EC2 deployment...\n")
    
    # User-data scripts for auto install 
    mysql_ud = """#!/bin/bash 
    apt update -y 
    apt install -y mysql-server
    systemctl enable mysql
    systemctl start mysql """ 
    
    proxy_ud = """#!/bin/bash
    apt update -y
    apt install -y python3 python3-pip
    pip3 install flask requests """ 
    
    gk_ud = """#!/bin/bash
    apt update -y
    apt install -y python3 python3-pip
    pip3 install flask requests """ 
    
    # Launch DB nodes
    db1 = launch_instance(keyname, ec2, sg_id, "t2.micro", "db-manager", mysql_ud)
    db2 = launch_instance(keyname, ec2, sg_id, "t2.micro", "db-worker-1", mysql_ud)
    db3 = launch_instance(keyname, ec2, sg_id, "t2.micro", "db-worker-2", mysql_ud) 
    
    # Launch proxy + gatekeeper
    proxy = launch_instance(keyname, ec2, sg_id, "t2.large", "proxy", proxy_ud)
    gatekeeper = launch_instance(keyname, ec2, sg_id, "t2.large", "gatekeeper", gk_ud) 
    
    print(" All instances are lanched ")
    
    if __name__ == "__main__": 
        parser = argparse.ArgumentParser(description="Launch EC2 instances") 
        parser.add_argument("--keyname", required=True, help="EC2 key pair name") 
        args = parser.parse_args() 
        main(args.keyname)