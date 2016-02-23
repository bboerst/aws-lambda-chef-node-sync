from chef import autoconfigure, Node

import chef
import boto3

def lambda_handler(event, context):

    ec2c = boto3.client('ec2')
    api = chef.autoconfigure()
    chef_nodes = {}
    aws_is_running = []
    nodes_to_remove = []

    #Array of running ec2 instances - ip addresses
    for region in ec2c.describe_regions()['Regions']:
        ec2 = boto3.resource('ec2', region_name=region['RegionName'])
        for instance in ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]):
            #print('Debug EC2 Instances: ', region['RegionName'], instance.private_ip_address)
            aws_is_running.append(instance.private_ip_address)

    #Dictionary of ip addresses (key) and Node objects (value) from Chef
    for name, nodeobj in Node.list().iteritems() :
        for key, value in nodeobj.attributes.iteritems():
            if key == 'ipaddress' :
                #print('Debug Chef Nodes: ', value, nodeobj)
                chef_nodes.update({value : nodeobj})

    #Calculating nodes to remove
    for key, node in chef_nodes.iteritems():
        if key not in aws_is_running:
            nodes_to_remove.append(node)

    #Removing nodes in Chef that are no longer in AWS
    for node in nodes_to_remove:
        #print('Debug Nodes to Remove:', node['ipaddress'])
        node.delete()

    #So that the removed nodes are logged
    print 'Removed', [x['ipaddress'] for x in nodes_to_remove]

    return 'Removed', [x['ipaddress'] for x in nodes_to_remove]