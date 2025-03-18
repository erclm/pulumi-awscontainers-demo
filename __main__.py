"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws
import pulumi_docker as docker
import json

# configs
config = pulumi.Config()
message = config.require("appMessage")
region = aws.config.region

repo = aws.ecr.Repository("apprepo")

repoinfo = repo.repository_url.apply(
    lambda url: {
        "server": url.split("/")[0],
        "repository": url.split("/")[1],
    }
)

image = docker.Image(
    "myappimage", 
    build=docker.DockerBuild(context="."), 
    image_name=repo.repository_url, 
    registry=docker.ImageRegistry(
        server=repoinfo["server"],username=aws.ecr.get_authorization_token().user_name,password=aws.ecr.get_authorization_token().password)
)

default_vpc = aws.ec2.get_vpc(default=True)
default_subnet_ids = aws.ec2.get_subnet_ids(vpc_id=default_vpc.id)

# thank you cursor
sg = aws.ec2.SecurityGroup(
    "app-sg",
    vpc_id=default_vpc.id,
    description="Allow HTTP",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
)

cluster = aws.ecs.Cluster("app-cluster")

task_definition = aws.ecs.TaskDefinition(
    "app-task",
    family="app-task",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=aws.iam.Role("task-execution-role", assume_role_policy=json.dumps({
        "Version": "2008-10-17",
        "Statement": [{
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": ""
            }]
    }
    )).arn,
    container_definitions=image.image_name.apply(
        lambda image_name: json.dumps([{
            "name": "app-container",
            "image": image_name,
            "essential": True,
            "portMappings": [{
                "containerPort": 8080,
                "hostPort": 8080,
                "protocol": "tcp"
            }],
            "environment": [
                {
                    "name": "APP_MESSAGE",
                    "value": message
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": aws.cloudwatch.LogGroup("app-log-group").name,
                    "awslogs-region": region,
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }])
    )
)

# Add permissions for the task execution role
exec_policy_attachment = aws.iam.RolePolicyAttachment(
    "task-exec-policy",
    role=task_definition.execution_role_name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
)

# Create the load balancer
lb = aws.lb.LoadBalancer(
    "app-lb",
    load_balancer_type="application",
    security_groups=[sg.id],
    subnets=default_subnet_ids.ids,
)

# Create target group
target_group = aws.lb.TargetGroup(
    "app-tg",
    port=80,
    protocol="HTTP",
    target_type="ip",
    vpc_id=default_vpc.id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        path="/",
        port="8080",
        protocol="HTTP",
        matcher="200",
        interval=30,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=2,
    ),
)

# Create a listener for the load balancer that forwards traffic to the target group
listener = aws.lb.Listener(
    "app-listener",
    load_balancer_arn=lb.arn,
    port=80,
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=target_group.arn,
        )
    ],
)

# Create ECS service
service = aws.ecs.Service(
    "app-service",
    cluster=cluster.arn,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=True,
        subnets=default_subnet_ids.ids,
        security_groups=[sg.id],
    ),
    load_balancers=[
        aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=target_group.arn,
            container_name="app-container",
            container_port=8080,
        )
    ],
    opts=pulumi.ResourceOptions(depends_on=[listener]),
)

# Export the endpoint
pulumi.export("url", lb.dns_name.apply(lambda dns_name: f"http://{dns_name}"))
