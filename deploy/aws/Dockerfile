FROM public.ecr.aws/docker/library/node:20-bookworm-slim

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl gh git jq python3 python3-pip python3-venv \
    && python3 -m pip install --break-system-packages --no-cache-dir boto3 pytest \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 factory \
    && useradd --uid 10001 --gid 10001 --create-home --shell /bin/bash factory

WORKDIR /opt/software-refactory
COPY factory/ /opt/software-refactory/factory/
COPY deploy/aws/entrypoint.sh /usr/local/bin/factory-cloud-entrypoint
RUN chmod +x /opt/software-refactory/factory/factory \
    /opt/software-refactory/factory/bedrock_adapter.py \
    /usr/local/bin/factory-cloud-entrypoint \
    && chown -R factory:factory /opt/software-refactory /home/factory

ENV HOME=/home/factory \
    PYTHONUNBUFFERED=1 \
    PORT=5050

USER factory
EXPOSE 5050
ENTRYPOINT ["/usr/local/bin/factory-cloud-entrypoint"]
