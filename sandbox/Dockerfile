FROM localstack/localstack-light:latest

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.2.2 \
    TERRAFORM_VERSION=1.0.0


RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install -y bash \
    git \
    gcc \
    python3-dev \
    libc-dev \
    zip \
    wget

RUN wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
RUN unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip && rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip
RUN mv terraform /usr/bin/terraform

RUN pip install "poetry==$POETRY_VERSION"

COPY entrypoint.sh /usr/local/bin/
COPY proxy /code/proxy/
COPY dist /code/dist/

WORKDIR /code/proxy/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

EXPOSE 8000
ENTRYPOINT ["entrypoint.sh"]
