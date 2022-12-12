import os

from aws_cdk import (
    Stack,
    aws_s3,
    RemovalPolicy,
    aws_events,
    aws_iam,
    aws_lambda,
    aws_events_targets,
    Size,
    Duration,
    CfnOutput,
)
from constructs import Construct


class CdkLambdaPythonStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        name_prefix: str,
        main_resources_name: str,
        deployment_environment: str,
        **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.construct_id = construct_id
        self.name_prefix = name_prefix
        self.main_resources_name = main_resources_name
        self.deployment_environment = deployment_environment

        # S3 bucket creation
        self.create_s3()

        # EventBridge Rule (CRON) creation
        self.create_events_rule()
        self.create_policy_statement_for_events_invoke()

        # Lambda function creation
        self.create_policy_statement_for_lambda()
        self.create_lambda_role_policy()
        self.create_lambda_role()
        self.create_docker_lambda_function()

        # Relevant CloudFormation outputs
        self.show_cloudformation_outputs()


    def create_s3(self):
        """
        Method that creates the S3 bucket.
        """
        self.bucket = aws_s3.Bucket(
            self,
            id=self.construct_id,
            bucket_name="{}{}-{}".format(self.name_prefix, self.main_resources_name, Stack.of(self).account),
            versioned=False,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            object_ownership=aws_s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
        )


    def create_events_rule(self):
        """
        Method to create AWS Event Rule for scheduling the Lambda function 
        based on a CRON approach.
        """
        # Runs every day at given UTC time
        self.rule = aws_events.Rule(
            self,
            id="{}Rule".format(self.construct_id),
            rule_name="{}{}-Rule".format(self.name_prefix, self.main_resources_name),
            description="Event rule for automatically triggering {} function based on cron.".format(self.main_resources_name),
            schedule=aws_events.Schedule.cron(
                minute='0',
                hour='3',
                month='*',
                week_day='FRI#1',
                year='*'
            )
        )


    def create_policy_statement_for_events_invoke(self):
        """
        Method to create IAM policy statement for event rule that invokes Lambda function.
        """
        self.events_invoke_policy_statement = aws_iam.PolicyStatement(
            actions=["lambda:InvokeFunction"],
            effect=aws_iam.Effect.ALLOW,
            resources=[self.rule.rule_arn]
        )


    def create_policy_statement_for_lambda(self):
        """
        Method to create IAM policy statement for Lambda execution.
        """
        self.s3_access_policy_statement = aws_iam.PolicyStatement(
            actions=[
                "s3:*",
                "ses:*",
            ],
            effect=aws_iam.Effect.ALLOW,
            resources=[
                "*",
            ],
        )


    def create_lambda_role_policy(self):
        """
        Method to create IAM Policy based on all policy statements.
        """
        self.lambda_role_policy = aws_iam.Policy(
            self,
            id="{}-Policy".format(self.construct_id),
            policy_name="{}{}-Policy".format(self.name_prefix, self.main_resources_name),
            statements=[
                self.s3_access_policy_statement,
                self.events_invoke_policy_statement,
            ],
        )


    def create_lambda_role(self):
        """
        Method that creates the role for Lambda function execution.
        """
        self.lambda_role = aws_iam.Role(
            self,
            id="{}-Role".format(self.construct_id),
            role_name="{}{}-Role".format(self.name_prefix, self.main_resources_name),
            description="Role for {}".format(self.main_resources_name),
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                aws_iam.ServicePrincipal("events.amazonaws.com"),
            ),
            managed_policies=[aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")],
        )

        self.lambda_role.attach_inline_policy(self.lambda_role_policy)
        self.lambda_role.add_managed_policy(aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))


    def create_docker_lambda_function(self):
        """
        Method that creates the main Lambda function based on a Docker image.
        """
        # Get relative path for folder that contains Lambda function sources
        # ! Note--> we must obtain parent dirs to create path (that's why there is "os.path.dirname()")
        PATH_TO_FUNCTION_FOLDER = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "lambdas",
            "python",
        )
        print("Source code for lambda function obtained from: ", PATH_TO_FUNCTION_FOLDER)

        self.docker_lambda_function = aws_lambda.DockerImageFunction(
            self,
            id="{}-Lambda".format(self.construct_id),
            code=aws_lambda.DockerImageCode.from_image_asset(PATH_TO_FUNCTION_FOLDER),
            function_name="{}{}".format(self.name_prefix, self.main_resources_name),
            environment={
                "OWNER": "Raja",
                "ENVIRONMENT": self.deployment_environment,
                "MAIN_URL": "https://data.cms.gov/provider-characteristics/medicare-provider-supplier-enrollment/medicare-fee-for-service-public-provider-enrollment",
                "S3_BUCKET_NAME": self.bucket.bucket_name,
                "OUTPUT_FOLDER": "/tmp/files",
                "FROM_EMAIL": "san99tiagodevsecops2@gmail.com",
                "TO_EMAILS_LIST": "san99tiagodevsecops@gmail.com,san99tiagodevsecops2@gmail.com",
                "SES_CONFIG_SET_NAME": "npi-emails",
            },
            description="Lambda Docker-Python function for {}".format(self.main_resources_name),
            role=self.lambda_role,
            timeout=Duration.minutes(8),
            memory_size=1024,
            ephemeral_storage_size=Size.mebibytes(2048),
        )

        self.docker_lambda_function.add_alias(self.deployment_environment)

        # Add Lambda function as a target for Event Rule 
        self.rule.add_target(aws_events_targets.LambdaFunction(self.docker_lambda_function))


    def show_cloudformation_outputs(self):
        """
        Method to create/add the relevant CloudFormation outputs.
        """

        CfnOutput(
            self,
            "DeploymentEnvironment",
            value=self.deployment_environment,
            description="Deployment environment",
        )

        CfnOutput(
            self,
            "LambdaFunctionARN",
            value=self.docker_lambda_function.function_arn,
            description="ARN of the created Lambda function",
        )

        CfnOutput(
            self,
            "LambdaFunctionRoleARN",
            value=self.docker_lambda_function.role.role_arn,
            description="Role for the created Lambda function",
        )
