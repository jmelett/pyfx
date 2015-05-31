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
ADD ta-lib.tar.gz /src
RUN cd /src/ta-lib && \
	./configure --prefix=/usr && \
	make && \
	make install && \
	cd / && \
	rm -rf /src

RUN pip install -U pip wheel Cython==0.22 numpy==1.9.2
