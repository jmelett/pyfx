FROM python:2.7.9

ENV DEBIAN_FRONTEND noninteractive

# Install OS level deps
#RUN apt-get update
#RUN apt-get install -y \

# Prepare the environment
ENV DOCKER 1
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Install TA-lib
ADD deps/ta-lib.tar.gz /src
RUN cd /src/ta-lib && \
	./configure --prefix=/usr && \
	make && \
	make install && \
	cd / && \
	rm -rf /src

# Install the app
COPY requirements.txt /usr/src/app/requirements.txt
RUN pip install --no-index --trusted-host pi.dev --find-links=http://pi.dev -r requirements.txt
