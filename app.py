#!/usr/bin/env python3
import os

from aws_cdk import (
    core as cdk,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_autoscaling as autoscaling
)

# For consistency with TypeScript code, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core

from vault_cluster_asg.vault_cluster_asg_stack import VaultClusterAsgStack

class VaultClusterAsgStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create custom VPC
        vpc = ec2.Vpc(self, "PhoenixVeritasCustomVPC",
                cidr="13.0.0.0/16",
                nat_gateways=0,
                subnet_configuration=[
                    ec2.SubnetConfiguration(
                        name="public",
                        cidr_mask=24,
                        subnet_type=ec2.SubnetType.PUBLIC),
                    ec2.SubnetConfiguration(
                        name="isolated",
                        cidr_mask=24,
                        subnet_type=ec2.SubnetType.ISOLATED)]
            )

        # Attach a public subnet to the ec2 instance
        vpc_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)

        # Use custom ubuntu image
        ubuntu_linux = ec2.MachineImage.generic_linux({
            "us-east-2": "ami-0a0591de7c3c8aee9"
        })

        # Setup System Manager Instance Profile
        role = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        # Auto-scaling group for Vault cluster
        asg = autoscaling.AutoScalingGroup(self, "VaultASG",
            role=role,
            vpc=vpc,
            vpc_subnets=vpc_subnets,
            instance_type=ec2.InstanceType(instance_type_identifier="t3.small"),
            machine_image=ubuntu_linux,
            desired_capacity=3,
            max_capacity=3,
            min_capacity=1
        )

        scaling_action = autoscaling.StepScalingAction(self,
            "scaleout",
            auto_scaling_group=asg,
            adjustment_type=autoscaling.AdjustmentType.EXACT_CAPACITY)

        scaling_action.add_adjustment(adjustment=1, lower_bound=1)

#        instance = ec2.Instance(self, "Instance",
#            instance_type=ec2.InstanceType("t3.nano"),
#            machine_image=ubuntu_linux,
#            vpc = vpc,
#            vpc_subnets=vpc_subnets,
#            role = role
#            )

app = core.App()
VaultClusterAsgStack(app, "VaultClusterAsgStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=core.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=core.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

app.synth()
