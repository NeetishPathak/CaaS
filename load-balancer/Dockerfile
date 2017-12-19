# The Dockerfile


FROM python:3
MAINTAINER CSC547-Fall-2017-Grp-3

RUN pip install requests flask

RUN mkdir -p /usr/load-balancer/app && \
	mkdir -p /usr/load-balancer/lib

COPY app/ /usr/load-balancer/app/
COPY lib/ /usr/load-balancer/lib/
COPY python.pth /usr/local/lib/python3.6/site-packages/

EXPOSE 8081 8081
WORKDIR /usr/load-balancer/

CMD /usr/local/bin/python3 /usr/load-balancer/app/load-balancer.py
