# pytest configuration file
import os

os.environ.update(
    {
        "AWS_REGION": "eu-west-2",
        "PREFIX": "nrlf",
        "ENVIRONMENT": "production",
        "SPLUNK_INDEX": "logs",
        "SOURCE": "app",
        "AUTH_STORE": "auth-store",
        "AWS_DEFAULT_REGION": "eu-west-2",
    }
)
