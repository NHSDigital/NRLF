
ENV ?= dev
ENV_NAME ?= $(shell (whoami || hostname ) | head -c 5)-$(ENV)
ENV_ACCOUNT_ID ?= $(shell aws secretsmanager get-secret-value --secret-id nhsd-nrlf--mgmt--$(ENV)-account-id --query SecretString --output text)

build-artifacts:
	(cd ../.. && $(MAKE) build)

init:
	(cd ../.. && $(MAKE) ENV=$(ENV) truststore-pull-server)
	terraform init
	terraform workspace select $(ENV_NAME) \
		|| terraform workspace new $(ENV_NAME)

plan:
	terraform plan \
		-var-file=./etc/$(ENV).tfvars \
		-var 'assume_role_arn=arn:aws:iam::$(ENV_ACCOUNT_ID):role/terraform'

apply:
	terraform apply \
		-var-file=./etc/$(ENV).tfvars \
		-var 'assume_role_arn=arn:aws:iam::$(ENV_ACCOUNT_ID):role/terraform'

destroy:
	terraform destroy \
		-var-file=./etc/$(ENV).tfvars \
		-var 'assume_role_arn=arn:aws:iam::$(ENV_ACCOUNT_ID):role/terraform'
