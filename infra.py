import boto3
import time
import urllib.request


ec2 = boto3.client('ec2', region_name='us-east-1')

# Variables pour stocker les IDs

igw_id = None
nat_gw_id = None
eip_allocation_id = None

# Subnets
public_subnet_1 = None
public_subnet_2 = None
private_app_subnet_1 = None
private_app_subnet_2 = None
private_db_subnet_1 = None
private_db_subnet_2 = None

# Route Tables
public_rt_id = None
private_app_rt_id = None
private_db_rt_id = None

# Security Groups
web_sg_id = None
app_sg_id = None
db_sg_id = None

# NACL
db_nacl_id = None

#=======Création du Vpc======

print("Creation du VPC...")

# 1. Créer le VPC
vpc_response = ec2.create_vpc(CidrBlock='10.0.0.0/16')
vpc_id = vpc_response['Vpc']['VpcId']
print(f"VPC créé : {vpc_id}")

# Ajouter un tag
ec2.create_tags(
    Resources=[vpc_id],
    Tags=[{'Key': 'Name', 'Value':'MyCustomVPC-Manual'}]
)

# 2. Activer les DNS hostnames

ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})



# ========== PHASE 2 : INTERNET GATEWAY ==========
print("Creation de l'Internet Gateway...")


# 4. Créer Internet Gateway
igw_response = ec2.create_internet_gateway()
igw_id = igw_response['InternetGateway']['InternetGatewayId']
print(f"IGW créé : {igw_id}")

#ajouter un tag
ec2.create_tags(
    Resources=[igw_id],
    Tags=[{'Key': 'Name', 'Value': 'MyCustomVPC-IGW'}]
)

 # 5. Attacher l'IGW au VPC
ec2.attach_internet_gateway(
     InternetGatewayId=igw_id,
     VpcId=vpc_id
 )

print("IGW attaché au VPC")



 # ========== PHASE 3 : SUBNETS ==========

print("Creation des subnets...")

# Public Subnet -AZ1
response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.1.0/24',
    AvailabilityZone='us-east-1a'
)
public_subnet_1 = response['Subnet']['SubnetId']
print(f"Public Subnet 1 créé : {public_subnet_1}")

# Public Subnet AZ2

response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.2.0/24',
    AvailabilityZone='us-east-1b'
)
public_subnet_2 = response['Subnet']['SubnetId']
print(f"Public Subnet 2 créé : {public_subnet_2}")

# Private-App-Subnet-AZ1

response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.3.0/24',
    AvailabilityZone='us-east-1a'
)
private_app_subnet_1 = response['Subnet']['SubnetId']
print(f"Private Subnet 3 créé : {private_app_subnet_1}")

# Private-App-Subnet-AZ2

response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.4.0/24',
    AvailabilityZone='us-east-1b'
)
private_app_subnet_2 = response['Subnet']['SubnetId']
print(f"Private Subnet 4 créé : {private_app_subnet_2}")

# Private-DB-Subnet-AZ1

response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.5.0/24',
    AvailabilityZone='us-east-1a'
)
private_db_subnet_1 = response['Subnet']['SubnetId']
print(f"private_db_subnet_1 créé : {private_db_subnet_1}")

# Private-DB-Subnet-AZ2

response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.6.0/24',
    AvailabilityZone='us-east-1b'
)
private_db_subnet_2 = response['Subnet']['SubnetId']
print(f"private_db_subnet_2 créé : {private_db_subnet_2}")


# Activer auto-assign IP publique pour les subnets publics
ec2.modify_subnet_attribute(SubnetId=public_subnet_1, MapPublicIpOnLaunch={'Value': True})
ec2.modify_subnet_attribute(SubnetId=public_subnet_2, MapPublicIpOnLaunch={'Value': True})
print("Auto-assign IP publique activé sur les subnets publics")


# ========== PHASE 4 : NAT GATEWAY ==========
print("Creation du NAT Gateway...")

# Allouer Elastic IP
response = ec2.allocate_address(Domain='vpc')
eip_allocation_id = response['AllocationId']

# Creer NAT Gateway

print("Creation du NAT Gateway...")

response = ec2.create_nat_gateway(
    SubnetId=public_subnet_1,  # DOIT etre dans un subnet PUBLIC
    AllocationId=eip_allocation_id,
    TagSpecifications=[{
        'ResourceType': 'natgateway',
        'Tags': [{'Key': 'Name', 'Value': 'MyCustomVPC-NAT'}]
    }]
)

nat_gw_id = response['NatGateway']['NatGatewayId']

# Attendre que le NAT  soit up
waiter = ec2.get_waiter('nat_gateway_available')
waiter.wait(NatGatewayIds=[nat_gw_id])
print("NAT Gateway disponible !")

#ATTENTION : Le NAT Gateway doit etre dans un subnet PUBLIC !
#Il permet aux subnets PRIVES d'acceder a Internet (sortant uniquement).


# ========== PHASE 5 : ROUTE TABLES ==========
print("Creation des tables de routes ...")



# Creer Route Table
response = ec2.create_route_table(
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'route-table',
        'Tags': [{'Key': 'Name', 'Value': 'Public-Route-Table'}]
    }]
)
public_rt_id = response['RouteTable']['RouteTableId']

# Ajouter route vers Internet
ec2.create_route(
    RouteTableId=public_rt_id,
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=igw_id
)


# Associer aux subnets publics
ec2.associate_route_table(RouteTableId=public_rt_id, SubnetId=public_subnet_1)
ec2.associate_route_table(RouteTableId=public_rt_id, SubnetId=public_subnet_2)
print(f"Public Route Table créée : {public_rt_id}")


# Private App Route Table
response = ec2.create_route_table(
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'route-table',
        'Tags': [{'Key': 'Name', 'Value': 'Private-App-Route-Table'}]
    }]
)
private_app_rt_id = response['RouteTable']['RouteTableId']

#Route vers le Nat

ec2.create_route(
    RouteTableId=private_app_rt_id,
    DestinationCidrBlock='0.0.0.0/0',
    NatGatewayId=nat_gw_id
)
# Associer aux subnets App
ec2.associate_route_table(RouteTableId=private_app_rt_id, SubnetId=private_app_subnet_1)
ec2.associate_route_table(RouteTableId=private_app_rt_id, SubnetId=private_app_subnet_2)
print(f'Private App Table créée: {private_app_rt_id} ')

# Private DB Route Table
response = ec2.create_route_table(
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'route-table',
        'Tags': [{'Key': 'Name', 'Value': 'Private-DB-Route-Table'}]
    }]
)
private_db_rt_id = response['RouteTable']['RouteTableId']

# PAS de route vers Internet - isolation totale

# Associer aux subnets DB
ec2.associate_route_table(RouteTableId=private_db_rt_id, SubnetId=private_db_subnet_1)
ec2.associate_route_table(RouteTableId=private_db_rt_id, SubnetId=private_db_subnet_2)
print(f'Private DB Route Table créée: {private_db_rt_id}')



# ========== PHASE 6 : SECURITY GROUPS ==========
print("Creation des Security Groups")



# Web Tier Security Group

my_ip = urllib.request.urlopen('https://checkip.amazonaws.com').read().decode().strip()

response = ec2.create_security_group(
    GroupName='Web-Tier-SG',
    Description='Security group for web servers in public subnets',
    VpcId=vpc_id
)
web_sg_id = response['GroupId']
print(f"Web SG créé : {web_sg_id}")


#Ouverture des  ports 

ec2.authorize_security_group_ingress(
    GroupId=web_sg_id,        # Sur quel SG
    IpProtocol='tcp',         # Protocole (tcp, udp, icmp)
    FromPort=80,              # Port de début
    ToPort=80,                # Port de fin
    CidrIp='0.0.0.0/0'        # Depuis quelle IP (0.0.0.0/0 = tout Internet)
)

ec2.authorize_security_group_ingress(
    GroupId=web_sg_id,        
    IpProtocol='tcp',         
    FromPort=443,              
    ToPort=443,                
    CidrIp='0.0.0.0/0'    
)

ec2.authorize_security_group_ingress(
    GroupId=web_sg_id,        
    IpProtocol='tcp',         
    FromPort=22,              
    ToPort=22,                
    CidrIp=f'{my_ip}/32'    
)    
print("Ports 80, 443, 22 ouverts sur Web SG")


#App Tier Security Group

response = ec2.create_security_group(
    GroupName='App-Tier-SG',
    Description='Security group for App servers in private subnets',
    VpcId=vpc_id
)
app_sg_id = response['GroupId']
print(f"App SG créé : {app_sg_id}")

ec2.authorize_security_group_ingress(
    GroupId=app_sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 8080,
        'ToPort': 8080,
        'UserIdGroupPairs': [{'GroupId': web_sg_id}]
    }]
)

ec2.authorize_security_group_ingress(
    GroupId=app_sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 22,
        'ToPort': 22,
        'UserIdGroupPairs': [{'GroupId': web_sg_id}]
    }]
)
print("Ports 8080, 22 ouverts sur App SG")

#Database Tier Security Group

response = ec2.create_security_group(
    GroupName='Database-Tier-SG',
    Description='Security group for database servers in private DB subnets',
    VpcId=vpc_id
)
db_sg_id = response['GroupId']
print(f"DB SG créé : {db_sg_id}")

ec2.authorize_security_group_ingress(
    GroupId=db_sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 3306,
        'ToPort': 3306,
        'UserIdGroupPairs': [{'GroupId': app_sg_id}]
    }]
)
print("Port 3306 ouvert sur Database SG")


# ========== PHASE 7 : NETWORK ACL ==========
print("Creation du Network ACL")


response = ec2.create_network_acl(
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'network-acl',
        'Tags': [{'Key': 'Name', 'Value': 'Database-NACL'}]
    }]
)
db_nacl_id = response['NetworkAcl']['NetworkAclId']
print(f"NACL créé : {db_nacl_id}")


ec2.create_network_acl_entry(
    NetworkAclId=db_nacl_id,
    RuleNumber=100,           # Priorité (plus petit = traité en premier)
    Protocol='6',             # 6 = TCP
    RuleAction='allow',       # allow ou deny
    Egress=False,             # False = Inbound (entrant)
    CidrBlock='10.0.3.0/22',  # Depuis les subnets App
    PortRange={'From': 3306, 'To': 3306}
)

ec2.create_network_acl_entry(
    NetworkAclId=db_nacl_id,
    RuleNumber=100,
    Protocol='6',
    RuleAction='allow',
    Egress=True,              # True = Outbound (sortant)
    CidrBlock='10.0.3.0/22',
    PortRange={'From': 1024, 'To': 65535}
)


# Trouver les associations actuelles des subnets DB
response = ec2.describe_network_acls(
    Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
)

# Pour chaque subnet DB, remplacer l'association
for nacl in response['NetworkAcls']:
    for assoc in nacl['Associations']:
        if assoc['SubnetId'] in [private_db_subnet_1, private_db_subnet_2]:
            ec2.replace_network_acl_association(
                AssociationId=assoc['NetworkAclAssociationId'],
                NetworkAclId=db_nacl_id
            )

print("NACL associé aux subnets DB")




# ========== VERIFICATION ==========
print("\n" + "="*50)
print("INFRASTRUCTURE CREEE AVEC SUCCES !")
print("="*50)
print(f"VPC: {vpc_id}")
print(f"Internet Gateway: {igw_id}")
print(f"NAT Gateway: {nat_gw_id}")
print(f"\nSubnets Publics: {public_subnet_1}, {public_subnet_2}")
print(f"Subnets App: {private_app_subnet_1}, {private_app_subnet_2}")
print(f"Subnets DB: {private_db_subnet_1}, {private_db_subnet_2}")
print(f"\nSecurity Groups:")
print(f"  Web: {web_sg_id}")
print(f"  App: {app_sg_id}")
print(f"  DB: {db_sg_id}")
print(f"\nNACL DB: {db_nacl_id}")
print("="*50)






















