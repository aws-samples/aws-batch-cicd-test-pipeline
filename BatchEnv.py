# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from aws_cdk import (
    aws_ec2,
    aws_events,
    aws_events_targets,
    aws_ssm,
    aws_ecr,
    aws_ecs
)
import aws_cdk.aws_batch_alpha as aws_batch
import aws_cdk as core
from constructs import Construct

class BatchEnvironment(core.Stack):

    def __init__(self, scope: Construct, id: str, namespace, ** kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # get the default VPC
        default_vpc = aws_ec2.Vpc(self, "VPC")

        # create a Batch compute environment with some default settings
        compute_environment = aws_batch.ComputeEnvironment(
            self, "Batch",
            compute_environment_name="MyComputeEnvironment",
            managed=True,
            compute_resources=aws_batch.ComputeResources(
                vpc=default_vpc,
                type=aws_batch.ComputeResourceType.SPOT,
                bid_percentage=100,
                allocation_strategy=aws_batch.AllocationStrategy.SPOT_CAPACITY_OPTIMIZED,
                maxv_cpus=256,
                minv_cpus=0,
                desiredv_cpus=0,
                compute_resources_tags=core.Tags.of(self).add('Name', 'BatchComputeInstance')
            ))

        # create the job queue and associate it to the CE just created
        job_queue = aws_batch.JobQueue(self, "JobQueue",
                                       job_queue_name="MyJobQueue",
                                       compute_environments=[aws_batch.JobQueueComputeEnvironment(
                                           compute_environment=compute_environment,
                                           order=1,)],
                                       enabled=True,
                                       priority=1)

        # get ecr repository project name
        ecr_repository_name = aws_ssm.StringParameter.value_for_string_parameter(
            self, f"{namespace}-ecrrepository")

        # get build project reference
        ecr_repository = aws_ecr.Repository.from_repository_name(
            self, id=f"ecr-repo-name-{id}", repository_name=ecr_repository_name)

        job_definition = aws_batch.JobDefinition(self, "JobDefinition",
                                                 job_definition_name="MyJobDefinition",
                                                 container={
                                                     "image": aws_ecs.EcrImage(ecr_repository, "latest"),
                                                     "vcpus": 4,
                                                     "memory_limit_mib": 256
                                                 })

        # create an events pattern triggered on new image push on the ecr repository
        event_pattern = aws_events.EventPattern(
            detail_type=['ECR Image Action'],
            detail={
                "result": ["SUCCESS"],
                "action-type": ["PUSH"],
                "image-tag": ["latest"],
                "repository-name": [ecr_repository_name]
            }
        )

        ecr_batch_trigger_rule = aws_events.Rule(
            self, "ECR to Batch Rule",
            description="Trigger a Batch job on push to ECR",
            event_pattern=event_pattern,
            targets=[aws_events_targets.BatchJob(
                job_queue_arn=job_queue.job_queue_arn,
                job_queue_scope=job_queue,
                job_definition_arn=job_definition.job_definition_arn,
                job_definition_scope=job_definition
            )])

        # outputs
        core.CfnOutput(
            self, "JobQueueName",
            description=f"Job Queue name {namespace}",
            value=job_queue.job_queue_name,
        )

        core.CfnOutput(
            self, "JobDefinitionName",
            description=f"Job definition name {namespace}",
            value=job_definition.job_definition_name
        )

    #   self.output_props['batch_job_queue'] = job_queue
    #   self.output_props['batch_job_def'] = job_definition

    # # pass objects to another stack
    # @property
    # def outputs(self):
    #   return self.output_props
