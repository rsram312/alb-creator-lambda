#!/usr/bin/env python3
"""Creates an ALB and attaches Target to Lambda

Event:
    String Parameters that need to be passed as part of the `aws lambda invoke` event payload
"""
import boto3
import random
from botocore.exceptions import ClientError

listenerArn = ""
targetGroupArn = ""

elbv2_client = boto3.client('elbv2','us-east-2')

# Initialize Globals to None
request_event = None

def get_tags_from_event():
    """List of tags
    
    Arguments:
        event {dict} -- Lambda event payload
    
    Returns:
        list -- List of AWS tags for use in a CFT
    """
    return [
        {
            "Key": "OwnerContact",
            "Value": request_event['OwnerContact']
        }
    ]

def create_load_balancer(params,tags):
    """Creating a Load balancer 
    Arguments:
        Name - Name of application load balancer
        Subnets - List of subnets
        Security Groups - List of SG's 
        Scheme - Default is internet facing. Available choices internal | internet-facing
        Type - Default is application
        IpAddressType - Default is Ipv4
    Returns:
        String - Load Balancer ARN 
    """
    
    load_balancer = elbv2_client.create_load_balancer(
        Name= search('AlbName',params) + '-alb',
        Subnets= search('SubnetIds',params).split(),
        SecurityGroups= search('SecurityGroups',params).split(),
        Scheme= search('Scheme',params),
        Tags= tags
        )
    return load_balancer['LoadBalancers'][0]['LoadBalancerArn']

def create_target_group(params):
    """ Creating a target group

   Arguments:
        Name - Name of the Target group (String)
        TargetType - Available options ip | lambda | instance
        Health Check Enabled - Boolean
        Health Check Path - Default is '/' 

    Returns:
        String - Target Group ARN 

    """
    target_group = elbv2_client.create_target_group(
        Name=search('AppName',params) + '-tg',
        TargetType=search('TargetType',params),
        HealthCheckEnabled=True if search('HealthCheckEnabled',params)=="True" else False,
        HealthCheckPath=search('HealthCheckPath',params)
    )
    return target_group['TargetGroups'][0]['TargetGroupArn']

def modify_target_group(targetGroupArn,params):
    """
        Modifies the existing target group
    """
    response = elbv2_client.modify_target_group(
        TargetGroupArn=targetGroupArn,
        HealthCheckEnabled=True if search('HealthCheckEnabled',params)=="True" else False,
        HealthCheckPath=search('HealthCheckPath',params)
    ) 
    return response['TargetGroups'][0]['TargetGroupArn']

def describe_target_group(params):
    """
    Arguments:
        Name - Name of the target Group

    Returns:
        Dict of the Target group attributes    
    """
    target_group = elbv2_client.describe_target_groups(
        Names=(search('AppName',params) + '-tg').split()
    )
    return target_group['TargetGroups'][0]['TargetGroupArn']

def create_rule(targetArn, listenerArn, params, priority):
    """ Creating a listener rule 
    Arguments:
        TargetGroupArn - ARN of the target group (String)
        ListenerArn - ARN of the listener (String)
        priority - Integer value of Listener rule priority

    Returns:
        Dict of the listener rules created 

    """
    listener_rules = elbv2_client.create_rule(
    Actions=[
        {
            'TargetGroupArn': targetArn,
            'Type': 'forward',
        },
    ],
    Conditions=[
        {
            'Field': 'path-pattern',
            'Values': search('rule_path',params).split(),
        },
    ],
    ListenerArn= listenerArn,
    Priority= priority
   )
    return listener_rules

def describe_rules(listenerArn):
    """
    Arguments:
        listenerArn - ARN of the listener (String)
    Returns:
        Describes the rules for the specified listener (Dict)
    """      
    response = elbv2_client.describe_rules(
        ListenerArn=listenerArn,
    )
    return response['Rules']    

def create_listener(targetArn,loadBalancerArn,params):
    """
    Arguments: 
        TargetGroupArn - ARN of the target group (String)
        LoadBalancerArn - ARN of the load balancer (String)
        
    Returns: 
        listenerArn - ARN of the listener created (String)
    """
    listener = elbv2_client.create_listener(
    DefaultActions=[
        {
            'TargetGroupArn': targetArn,
            'Type': 'forward',
        },
    ],
    Certificates=[ 
        {
            'CertificateArn': search('CertificateArn',params),
        },
    ],
    LoadBalancerArn= loadBalancerArn,
    Port=443,
    Protocol='HTTPS',
    SslPolicy=search('SslPolicy',params),
    )
    return listener['Listeners'][0]['ListenerArn']

def describe_listener(loadBalancerArn):
    """
    Arguements:
        loadBalancerArn - ARN of the Load balancer(String)
    Returns:
        Describes the listeners for the specified ALB (Dict) 
    """        
    response = elbv2_client.describe_listeners(
    LoadBalancerArn=loadBalancerArn,
    )
    return response['Listeners'][0]['ListenerArn']

def register_targets(targetArn, lambdaArn):
    """
    Arguments:
        TargetGroupArn - ARN of the target group (String)
        lambdaArn - ARN of the lambda function the target is getting registered to

    Returns: 
        null 
    """    

    response = elbv2_client.register_targets(
    TargetGroupArn= targetArn,
    Targets=[
        {
            'Id': lambdaArn,
        },
    ],
)
def add_lambda_permission(stack_name,targetGroupArn,priority):
    """
    Arguments:
        FunctionName - Lambda function name (String)
        SourceArn - ARN of the target group (String)
    """
        
    client = boto3.client('lambda')
    response = client.add_permission(
        Action='lambda:InvokeFunction',
        FunctionName=stack_name,
        Principal='elasticloadbalancing.amazonaws.com',
        SourceArn=targetGroupArn,
        StatementId=str(priority),
    )

def get_default_params(stack_name):      
    return [
            {'ParameterKey': 'AppName', 'ParameterValue': stack_name},
            {'ParameterKey': 'OwnerContact', 'ParameterValue': request_event['OwnerContact']},
            {'ParameterKey': 'IamRole', 'ParameterValue': request_event['IamRole']},
            {'ParameterKey': 'SubnetIds', 'ParameterValue': request_event['SubnetIds']},
            {'ParameterKey': 'SecurityGroups', 'ParameterValue': request_event['SecurityGroups']},
            {'ParameterKey': 'Scheme', 'ParameterValue': request_event.get('Scheme','internal')},
            {'ParameterKey': 'HealthCheckEnabled', 'ParameterValue': request_event.get('HealthCheckEnabled', 'True')},
            {'ParameterKey': 'HealthCheckPath', 'ParameterValue': request_event.get('HealthCheckPath', '/')},
            {'ParameterKey': 'TargetType', 'ParameterValue': request_event.get('TargetType', 'lambda')},
            {'ParameterKey': 'rule_path', 'ParameterValue': request_event['rule_path']},
            {'ParameterKey': 'AlbName', 'ParameterValue': request_event['AlbName']},
            {'ParameterKey': 'CertificateArn', 'ParameterValue': request_event['CertificateArn']},
            {'ParameterKey': 'SslPolicy', 'ParameterValue': request_event['SslPolicy']},
        ]
    
def search(ParameterKey, parameters):
    return ''.join([element['ParameterValue'] for element in parameters if element['ParameterKey'] == ParameterKey])
      
def do_it(event, context):
    global request_event
    request_event = event
    stack_name = request_event['AppName']
    params = get_default_params(stack_name)
    print("parameters:",params)
    custodian_tags = get_tags_from_event()
    try:
        targetGroupArn = create_target_group(params)
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'DuplicateTargetGroupName':
            targetArn = describe_target_group(params)
            print("TargetGroup already exists:",targetArn)
            targetGroupArn = modify_target_group(targetArn, params)
        else:
            raise ex   

    print("targetGroupArn:",targetGroupArn)
    loadBalancerArn = create_load_balancer(params, custodian_tags)
    print("loadBalancerArn:",loadBalancerArn)
    
    try:
        listenerArn = create_listener(targetGroupArn, loadBalancerArn, params)
    except (Exception) as ex:
        print("A listener already exists on this loadbalancer:",loadBalancerArn)
        listenerArn = describe_listener(loadBalancerArn)
        
    print("listenerArn:",listenerArn)
    priority = random.randint(10,500)

    rules = describe_rules(listenerArn)
    rule_path = search('rule_path',params).split()
    if not any(len(rule['Actions']) > 0 and rule['Actions'][0]['TargetGroupArn'] == targetGroupArn and len(rule['Conditions']) > 0 and rule['Conditions'][0]['Values'] == rule_path for rule in rules):
        listener_rules = create_rule(targetGroupArn,listenerArn, params, priority)
    else:
        print("Listener Rule with rule path already exists for the Target group")
    
    print("listener_rules: ", rules)
    
    add_lambda_permission(stack_name,targetGroupArn,priority)
    try:
        lambda_client = boto3.client('lambda')
        functionName = stack_name
        response = lambda_client.get_function(FunctionName=functionName)
        lambdaArn = response['Configuration']['FunctionArn']
    except ClientError as ex:
        raise ex  

    return register_targets(targetGroupArn, lambdaArn)