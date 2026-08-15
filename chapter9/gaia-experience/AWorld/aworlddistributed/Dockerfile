FROM python:3.11-slim-bookworm AS base


## Basis ##
ENV ENV=prod \
    PORT=9099

# Install GCC and build tools. 
# These are kept in the final image to enable installing packages on the fly.
RUN apt-get update && \
    apt-get install -y gcc build-essential curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y wget unzip openssh-client procps nodejs npm

ARG PIP_OPTIONS='-i https://mirrors.aliyun.com/pypi/simple/'
ARG ENABLE_OSS_MOUNT=""

RUN pip install -U pip pysocks ${PIP_OPTIONS}

# Install Chrome Driver
RUN mkdir /app

RUN cd /app/ && \
    wget https://storage.googleapis.com/chrome-for-testing-public/136.0.7103.92/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    rm chromedriver-linux64.zip
ENV CHROME_DRIVER_PATH=/app/chromedriver-linux64/chromedriver


RUN if [ "$ENABLE_OSS_MOUNT" = "true" ]; then \
        apt-get update && \
        apt-get install -y gdebi-core mime-support && \
        cd /tmp && \
        wget https://gosspublic.alicdn.com/ossfs/ossfs_1.91.6_ubuntu22.04_amd64.deb && \
        gdebi ossfs_1.91.6_ubuntu22.04_amd64.deb -n && \
        rm ossfs_1.91.6_ubuntu22.04_amd64.deb && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*; \
    fi

FROM base as runner

WORKDIR /app

# Install Python dependencies
COPY ./requirements.txt .
RUN pip3 install uv ${PIP_OPTIONS}
RUN uv pip install --system -r requirements.txt --no-cache-dir ${PIP_OPTIONS}

# Copy the application code
RUN echo "start install aworld"
RUN mkdir -p /app/lib
RUN cd /app/lib && git clone https://github.com/inclusionAI/AWorld.git
RUN cd /app/lib/AWorld && git checkout framework_upgrade_aworldserver_gaia && pip install -r aworld/requirements.txt ${PIP_OPTIONS} && python setup.py install

RUN npx playwright install chrome --with-deps --no-shell

RUN cd /app



# Layer on for other components
FROM runner AS app

WORKDIR /app

COPY . .

# Expose the port
ENV HOST="0.0.0.0"
ENV PORT="9099"

# if we already installed the requirements on build, we can skip this step on run
ENTRYPOINT [ "bash", "start.sh" ]
