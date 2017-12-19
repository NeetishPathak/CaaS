import os
import pdb
import json
import random
import subprocess as sp

from config import DEFAULT_RAM, DEFAULT_CPU, DOCKER_REGISTRY_URI, SERVER_SHARED_DIR, CON_SHARED_DIR, MASTER_SHARED_DIR
from config import DEFAULT_CONTAINER_USENAME, DEFAULT_CONTAINER_PASSWORD
from models import logger


class ContainerManager():
    """ A class which will interact with individual services on
        the compute nodes.
    """

    def __init__(self, database_manager):
        """ Initialize the available compute nodes
        :param database_manager:
        """
        self.database = database_manager

    def get_compute_node(self):
        # TODO: Current assumption is that each image is present on each node. This might not be the case.
        """
        #image = self.database.get_image(image_id)
        nodes = get the nodes which host this image.
        # This shall require change in DB model. Image name shouldn't be unique.
        """
        nodes = self.database.get_alive_computenodes()
        if not nodes:
            return None
        try:
            total_capacity = sum([node.compute_node_wt for node in nodes]) # Can't be zero
            total_load = sum([con.image.image_wt for node in nodes for con in node.container])  # Can be zero
            node_loads = []
            for node in nodes:
                optimal_load = node.compute_node_wt / total_capacity
                current_load = sum(con.image.image_wt for con in node.container) / total_load
                # If load_balance < 0 then the node is underloaded
                # If load_balance > 0 then the node is overloaded
                # Select the node with minimum load to host the new container
                load_balance = current_load - optimal_load
                node_loads.append((load_balance, node))
            optimal_node = min(node_loads, key=lambda x: x[0])
            return optimal_node[1]
        except ZeroDivisionError:
            return nodes[random.randint(0, nodes.count()-1)]

    @staticmethod
    def kill_container(container):
        output = ""
        base_cmd = "ssh -o StrictHostKeyChecking=no root@{0} ".format(container.node.ip_addr)
        stop_cmd = "docker stop {0}".format(container.container_id)
        try:
            output = sp.call("{0}{1}".format(base_cmd, stop_cmd), shell=True)
        except Exception as e:
            # Try to stop gracefully, if we can't, we'll kill it forcefully.
            logger.exception("Failed to stop. Command = {0}{1}\n{2}".format(base_cmd, stop_cmd, e))

        rm_cmd = "docker rm -f {0}".format(container.container_id)
        try:
            output = sp.call("{0}{1}".format(base_cmd, rm_cmd), shell=True)
            assert output == 0
        except Exception as e:
            logger.exception("Failed to remove container. {0}{1}\n{2}".format(base_cmd, stop_cmd, e))
            return False
        return True

    @staticmethod
    def run_container(image_name, compute_node_ip, ram, cpu, container_name=None):
        """
            Start a container related to the image_name on compute_node_ip
            TODO: SSH into compute_node_ip and execute the
            proper docker run command
            :param image_name: (string) Eg. Nginx
            :param compute_node_ip: (String) Eg. 10.0.0.1
            :param ram: Max ram for this container (in MB)
            :return: Status(Boolean), Docker port(Integer), container_name(str), container_id(str)
        """
        #pdb.set_trace()
        image_name = "{0}/{1}".format(DOCKER_REGISTRY_URI, image_name)
        base_cmd = "ssh -o StrictHostKeyChecking=no root@{0} ".format(compute_node_ip)
        pull_cmd = "docker pull {0}".format(image_name)
        try:
            # We don't the exception to be printed on master's screen, hence stdout=sp.PIPE
            output = sp.call("{0}{1}".format(base_cmd, pull_cmd), shell=True, stdout=sp.PIPE)
            if output != 0:
                logger.error("Failed: Pull image {0}".format(image_name))
        except Exception as e:
            logger.exception("Failed: command: {0}{1}\n{2}".format(base_cmd, pull_cmd,e))
            # It's ok to get an exception. Maybe the registry is down. Just try if the image
            # is in local storage.
            # return False, None, None, None

        # Once image has been pulled, run it.
        # We plan to restart the containers on a failed node to a live node.
        # Hence we don't want the --restart always option. Otherwise we will
        # have duplicate containers.
        TEMPORARY = "temporary"
        if container_name:  # If a container name has been given
            # Check if a shared dir already exists
            master_dir_name = os.path.join(MASTER_SHARED_DIR, container_name)
            host_mount_dir = os.path.join(SERVER_SHARED_DIR, container_name)
            container_name = "--name {0}".format(container_name)
        else:
            container_name = ""
            host_mount_dir = os.path.join(SERVER_SHARED_DIR, TEMPORARY )
            master_dir_name = os.path.join(MASTER_SHARED_DIR, TEMPORARY )
        if not os.path.exists(master_dir_name):
            os.mkdir(master_dir_name)
            os.chmod(master_dir_name, 0o777)
        shared_volume = "-v {0}:{1}".format(host_mount_dir, CON_SHARED_DIR)
        run_cmd = "docker run -P --detach --cpus {0} --memory {1}m {2} {3} {4}" \
                  .format(cpu, ram, container_name, shared_volume, image_name)
        try:
            print("{0}{1}".format(base_cmd, run_cmd))
            #exit()
            cont_id = sp.check_output("{0}{1}".format(base_cmd, run_cmd), shell=True).decode('utf-8')
            assert cont_id
        except Exception as e:
            logger.exception("Failed: {0}{1}\n{1}".format(base_cmd, run_cmd, e))
            return False, None, None, None

        inspect_cmd = "docker inspect {0}".format(cont_id)
        try:
            output = sp.check_output("{0}{1}".format(base_cmd, inspect_cmd), shell=True).decode('utf-8')
            data = json.loads(output)[0]
            cont_name = data['Name'][1:].strip()  # The output is "/some_name"
            docker_port = int(data['NetworkSettings']['Ports']['22/tcp'][0]['HostPort'])
            new_dir_name = os.path.join(MASTER_SHARED_DIR, cont_name)
            os.rename(master_dir_name, new_dir_name)
            logger.info("Successfully Launched Container. Name={0}, Mounted Dir {1}".format(cont_name, new_dir_name))
        except Exception as e:
            logger.exception("Failed: {0}{1}\n{2}".format(base_cmd, inspect_cmd, e))
            return False, None, None, None

        return True, docker_port, cont_name, cont_id.strip()

    def update_container_health(self, con_name, status):
        container = self.database.get_container_by_name(con_name)
        container.container_status = status
        self.database.db.session.commit()

    def delete_reservation(self, con_id):
        """
            1. Delete IP table rule on management node.
            2. SSH into compute node and kill docker container. exit
            3. Delete entry from containers table.
            :param con_id: Container id in the database
            :return: 0 on success
        """
        container = self.database.get_container(con_id.strip())
        status = self.database.delete_ssh_port_forward_rule(container)
        if status is False:
            logger.exception("Failed to delete IP table rule")
            return -1
        status = self.kill_container(container)
        if status is False:
            logger.error("Failed to kill container {0}".format(container))
            return -2
        status = self.database.remove_container(container)
        if status is True:
            return 0
        return -1

    def create_reservation(self, username, data, container_name=None):  # TODO:
        """
        ImmutableMultiDict([('images', 'mysql'),
        ('memoryRange', '1024'),
        ('cpuRange', '1'), ('start_date', ''), ('end_date', ''),
        ('time', 'now')])
        container_name, nat_port, management_ip,
           docker_port, ram, cpu=None, start_time=None,
           end_time, container_username, container_password)
        :return: 0 on success, -1 on failure
        """
        user = self.database.get_user_by_name(username)
        image = self.database.get_image_by_name(data['images'])
        ram = data.get('memoryRange', DEFAULT_RAM)
        cpu = data.get('cpuRange', DEFAULT_CPU)
        #pdb.set_trace()
        node = self.get_compute_node()
        if node is None:
            return -1
        try:
            status, docker_port, con_name, con_id = self.run_container(image.image_name, node.ip_addr, ram, cpu, container_name)
        except Exception as e:
            logger.exception("Failed to run container of image={0} on node {1}".format(image.image_name, node.ip_addr))
            return -2
        if status is True:
            nat_port, management_ip = self.database.add_ssh_port_forward_rule(node.ip_addr, docker_port)
            status = self.database.add_container(container_id=con_id, container_name=con_name,
                                        nat_port=nat_port, management_ip=management_ip,
                                        docker_port=docker_port, ram=ram,
                                        cpu=cpu, username=DEFAULT_CONTAINER_USENAME,
                                        password=DEFAULT_CONTAINER_PASSWORD,
                                        node=node, image=image, user=user)
            if status is True:
                return 0
        return -1

    def migrate_all_containers(self, node):
        """ Should be called when a compute node is down.
        :param node: The compute node whose containers are to be shifted.
        :return:
        """
        for con in node.container:
            logger.info("Migrating container {0}".format(con))
            if self.database.add_deleted_container(con) is False:
                continue
            status = self.database.delete_ssh_port_forward_rule(con)
            if status is False:
                logger.exception("Failed to delete IP table rule")
                return -1
            node = self.get_compute_node()
            if node is None:
                logger.exception("No available compute node available. Cannot migrate containers")
                return -1
            image_name, ram, cpu, con_name = con.image.image_name, con.ram, con.cpu, con.container_name
            try:
                status, docker_port, con_name, con_id = self.run_container(image_name, node.ip_addr, ram, cpu, con_name)
            except Exception as e:
                logger.exception("Failed to launch a new container of image {0} on Node: {1}", image_name, node.ip_addr)
                continue
            if status is True:
                nat_port = con.nat_port
                image = self.database.get_image(con.image.image_id)
                user = self.database.get_user(con.user.id)
                nat_port, management_ip = self.database.add_ssh_port_forward_rule(node.ip_addr, docker_port, nat_port=nat_port)
                status = self.database.remove_container(con)
                status = self.database.add_container(container_id=con_id, container_name=con_name,
                                                     nat_port=nat_port, management_ip=management_ip,
                                                     docker_port=docker_port, ram=ram,
                                                     cpu=cpu, username=DEFAULT_CONTAINER_USENAME,
                                                     password=DEFAULT_CONTAINER_PASSWORD,
                                                     node=node, image=image, user=user)
                if status is not True:
                    logger.error("Failed to add to Database")
                else:
                    logger.error("Successfully Migrated one container to {0}".format(node.ip_addr))

    def migrate_reservation(self, con_id):
        """ Should be called when a node hosting a container is unreachable.
        steps:
        :param con_id:
        :return:
        """
        pass
