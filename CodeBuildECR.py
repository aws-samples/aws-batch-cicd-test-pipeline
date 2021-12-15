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
    core,
    aws_s3,
    aws_codebuild,
    aws_ecr,
    aws_ssm,
)

class CodeBuildECRStack(core.Stack):

  def __init__(self, scope: core.Construct, id: str, namespace, ** kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    # ECR repository to push built containers
    ecr = aws_ecr.Repository(
        self, "ECR",
        repository_name=f"{namespace.lower()}",
        removal_policy=core.RemovalPolicy.DESTROY
    )

    # ssm parameter to get codebuild project name later
    bucket_parameter = aws_ssm.StringParameter(
        self, "ParameterECRBucket",
        parameter_name=f"{namespace}-ecrrepository",
        string_value=ecr.repository_name,
        description=f"ECR Repository for {namespace}"
    )

    # TODO: do we actually need this?
    # s3 bucket with generated name for the codebuild artifacts
    source_bucket = aws_s3.Bucket(
        self, "ArtifactsBucket",
        bucket_name=core.PhysicalName.GENERATE_IF_NEEDED,
        versioned=True,
        removal_policy=core.RemovalPolicy.DESTROY)

    # ssm parameter to get codebuild project name later
    bucket_parameter = aws_ssm.StringParameter(
        self, "ParameterBuildBucket",
        parameter_name=f"{namespace}-sourcebucket",
        string_value=source_bucket.bucket_name,
        description=f"Codebuild source bucket for {namespace}"
    )

    # codebuild project meant to run in pipeline
    # use the build spec
    cb_docker_build = aws_codebuild.PipelineProject(
        self, "DockerBuild",
        project_name=f"{namespace}-Docker-Build",
        environment=aws_codebuild.BuildEnvironment(
            privileged=True,
        ),
        # pass the ecr repo uri into the codebuild project so codebuild knows where to push
        environment_variables={
            'REPOSITORY_URI': aws_codebuild.BuildEnvironmentVariable(
                value=ecr.repository_uri),
            'AWS_DEFAULT_REGION': aws_codebuild.BuildEnvironmentVariable(
                value=self.region)
        },
        description=f"Codebuild pipeline for {namespace}",
        timeout=core.Duration.minutes(60),
    )
    # codebuild iam permissions to read write s3
    source_bucket.grant_read_write(cb_docker_build)

    # codebuild permissions to interact with ecr
    ecr.grant_pull_push(cb_docker_build)

    # ssm parameter to get codebuild project name later
    build_parameter = aws_ssm.StringParameter(
        self, "ParameterBuild",
        parameter_name=f"{namespace}-codebuild",
        string_value=cb_docker_build.project_name,
        description=f"Codebuild project for {namespace}"
    )

    # outputs
    core.CfnOutput(
        self, "EcrUri",
        description=f"URI for the ECR repository {namespace}",
        value=ecr.repository_uri,
    )

    # TODO: do we actually need this?
    core.CfnOutput(
        self, "ArtifactsS3Bucket",
        description=f"Artifacts S3 Bucket for pipeline {namespace}",
        value=source_bucket.bucket_name
    )

  #   self.output_props['cb_source_bucket'] = source_bucket
  #   self.output_props['cb_build_roject'] = cb_docker_build
  #   self.output_props['ecr_repository'] = ecr

  # # pass objects to another stack

  # @property
  # def outputs(self):
  #   return self.output_props
