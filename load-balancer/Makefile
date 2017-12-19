
# The file defines make commands for ease of developement.

build:
	docker build -t load-balancer .

run:
	docker run --rm -P -t load-balancer

rund:
	docker run -d --rm -P -t load-balancer

restart: build run

ID := $(shell docker ps | grep "load-balancer" | awk '{print $$1}')
getip:
	docker inspect $(ID) | grep "\"IPAddress"

stopdocker:
	docker stop $(shell docker ps | grep "0.0" | awk '{print $$1}')

cleanimage:
	docker rmi -f $(shell docker images | grep "none" | awk '{print $$3}')

cleancontainer:
	docker rm -f $(shell docker ps | grep "0.0" | awk '{print $$1}')
