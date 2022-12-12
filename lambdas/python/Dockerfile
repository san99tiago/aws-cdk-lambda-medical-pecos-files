FROM public.ecr.aws/lambda/python:3.9

LABEL maintainer="Santiago Garcia Arango [san99tiago]"

# Copy function code
COPY . ${LAMBDA_TASK_ROOT}

# Install python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Install necessary dependencies
RUN yum update -y && yum install -y wget unzip && yum clean all

RUN yum install -y atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel -y

# Install Chrome (Chromium) and ChromeDriver
ENV CHROMIUM_VERSION=1002910
COPY install-browser.sh /tmp/
RUN /usr/bin/bash /tmp/install-browser.sh

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.handler" ]
