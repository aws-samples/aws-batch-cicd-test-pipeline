#!/usr/bin/env python3

from aws_cdk import core

from CodeCommit import CodeCommitStack
from CodeBuildECR import CodeBuildECRStack
from CodePipeline import CodePipelineStack
from BatchEnv import BatchEnvironment


class CICDSoftwarePipeline(core.Construct):
    def __init__(self, scope, id, assets_directory):
        super().__init__(scope, id)

        # build the repository
        code = CodeCommitStack(app, f"{id}-code", id, assets_directory)

        # create the build project and associated artifacts directories
        build = CodeBuildECRStack(app, f"{id}-build", id)
        build.add_dependency(code)

        # build the pipeline stage
        pipeline = CodePipelineStack(app, f"{id}-pipeline", id)
        pipeline.add_dependency(build)

        batch = BatchEnvironment(app, f"{id}-batch", id)
        batch.add_dependency(build)


app = core.App()
CICDSoftwarePipeline(app, "CICDPipelineAWSBatch", 'app-package')
app.synth()
