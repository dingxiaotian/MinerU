# Use the official Ubuntu base image
FROM ubuntu:latest

# Set environment variables to non-interactive to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install necessary packages
RUN apt-get update && \
    apt-get install -y \
        software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
        python3.10 \
        python3.10-venv \
        python3.10-distutils \
        python3-pip \
        wget \
        git \
        libgl1 \
        libglib2.0-0 \
        && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Create a virtual environment for MinerU
RUN python3 -m venv /opt/mineru_venv

RUN /bin/bash -c "source /opt/mineru_venv/bin/activate"

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn

RUN pip install --upgrade pip
RUN pip install detectron2 --extra-index-url https://myhloli.github.io/wheels/
RUN pip install struct-eqtable pypandoc fastapi uvicorn requests python-multipart
# Install depends for magic-doc
RUN pip install func-timeout smart-open python-pptx python-docx

# Copy the configuration file template and set up the model directory
COPY magic-pdf.template.json /root/magic-pdf.json

# Set the models directory in the configuration file (adjust the path as needed)
RUN sed -i 's|/tmp/models|/opt/models|g' /root/magic-pdf.json

# Create the models directory
RUN mkdir -p /opt/models

# Set the entry point to activate the virtual environment and run the command line tool
ENTRYPOINT ["/bin/bash", "-c", "source /opt/mineru_venv/bin/activate && exec \"$@\"", "--"]
