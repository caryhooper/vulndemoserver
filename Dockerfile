FROM ubuntu
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -o Acquire::Check-Valid-Until="false" update
RUN	apt-get -o Acquire::Check-Valid-Until="false"  install -y nano git wget build-essential python3-dev python3-setuptools python3-wheel python3-cffi python3-pip libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info wkhtmltopdf sudo
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb || true
RUN apt --fix-broken -y install
RUN	apt-get -o Acquire::Check-Valid-Until="false" clean
EXPOSE 31337
RUN git clone https://github.com/caryhooper/vulndemoserver
WORKDIR /vulndemoserver
RUN pip3 install -r requirements.txt
CMD ["sudo","-u","vds","python3", "/vulndemoserver/vulndemoserver.py"]

