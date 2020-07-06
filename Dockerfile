FROM ubuntu
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
	apt-get install -y nano git wget build-essential python3-dev python3-setuptools python3-wheel python3-cffi python3-pip libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info && \
	apt-get clean
EXPOSE 31337
RUN git clone https://github.com/caryhooper/vulndemoserver
WORKDIR /vulndemoserver
RUN pip3 install -r requirements.txt
CMD ["python3", "/vulndemoserver/vulndemoserver.py"]

