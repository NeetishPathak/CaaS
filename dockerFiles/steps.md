Steps to run nginx container:

1. build container: docker build -t <image_name> -f ./<dockerfile> .
2. run conatiner: docker run -d -P --name <container_name> <image_name> 
3. to find docker port: docker port <container_name> 22
4. ssh credential: root:passwd123


Steps to upload an image in a docker registry:
We are running the registry on 10.0.0.1:5000
```
# Docker registry is on 10.0.0.1:5000
docker run -d -p 5000:5000 --name registry registry:2
docker build -t <image_name> -f ./<dockerfile> .
docker tag <image_name> 10.0.0.1:5000/<image_name>
docker push 10.0.0.1:5000/image_name
```

================
3. exec container: docker exec -it elastic_northcutt bash
4. in browser check localhost
5.
```
#Remove a container and its volumes
$ docker rm -v $(docker ps -a -q)
```
service nginx status


Ansible 
ansible --version

### Docker registry commands:
https://docs.docker.com/registry/

Removing containers.
https://zaiste.net/posts/removing_docker_containers/
