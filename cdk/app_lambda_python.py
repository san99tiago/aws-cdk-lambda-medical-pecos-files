#!/usr/bin/env python3
import os
import aws_cdk as cdk

import add_tags
from stacks.cdk_lambda_python_stack import CdkLambdaPythonStack


DEPLOYMENT_ENVIRONMENT = "prod"
NAME_PREFIX = ""
MAIN_RESOURCES_NAME = "pecos-quarterly-data"


app = cdk.App()

stack = CdkLambdaPythonStack(
    app,
    "{}-stack-cdk".format(MAIN_RESOURCES_NAME),
    NAME_PREFIX,
    MAIN_RESOURCES_NAME,
    DEPLOYMENT_ENVIRONMENT,
    env={
        "account": os.getenv("CDK_DEFAULT_ACCOUNT"), 
        "region": os.getenv("CDK_DEFAULT_REGION"),
    },
    description="Stack that creates the infrastructure to download PECOS files.",
)

add_tags.add_tags_to_stack(stack)

app.synth()
