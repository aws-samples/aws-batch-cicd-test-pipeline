# Creates a code commit repository
# If an asset directory is provided then use it to bootstrap the repository

from aws_cdk import (
    core,
    aws_codecommit,
    aws_ssm,
)

from aws_cdk.aws_s3_assets import Asset
import os.path
dirname = os.path.dirname(__file__)


class CodeCommitStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, namespace, assets_directory=None, ** kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # check if there is a directory to upload
        if assets_directory:
            # Archive and upload to Amazon S3 as a .zip file
            # the source directory should be relative to the files
            source_asset = Asset(self, f"SourceAssets-{assets_directory}",
                                 path=os.path.join(dirname, assets_directory)
                                 )

            # create a repository with the assets
            code = aws_codecommit.CfnRepository(
                self, "CodeCommitRepository",
                repository_name=f"{namespace}",
                repository_description=f"Code repository for {namespace}",
                code=aws_codecommit.CfnRepository.CodeProperty(
                    branch_name='main',
                    s3=dict(
                        bucket=source_asset.s3_bucket_name,
                        key=source_asset.s3_object_key)
                )
            )
        else:
            # create a repository without assets
            code = aws_codecommit.CfnRepository(
                self, "CodeCommitRepository",
                repository_name=f"{namespace}",
                repository_description=f"Code repository for {namespace}",
                code=aws_codecommit.CfnRepository.CodeProperty(
                    branch_name='main'
                )
            )

        # ssm parameter to get bucket name later
        repository_parameter = aws_ssm.StringParameter(
            self, "ParameterRepository",
            parameter_name=f"{namespace}-repository",
            string_value=code.repository_name,
            description=f"CodeCommit repository for {namespace}"
        )

        # outputs
        core.CfnOutput(
            self, f"CodeCommitRepositoryName",
            description=f"Repository name of {namespace}",
            value=code.repository_name,
        )

    #     self.output_props['repository_name'] = code

    # # pass objects to another stack
    # @property
    # def outputs(self):
    #     return self.output_props
