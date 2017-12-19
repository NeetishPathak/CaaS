import pdb
from models import db
from models import User, ComputeNode, Containers, Images
from lib.DatabaseManager import DatabaseManager
from lib.ContainerManager import ContainerManager

database = DatabaseManager(db)

users = database.get_all_users()
nodes = database.get_all_computenodes()
images = database.get_all_images()
containers = database.get_all_containers()
dels = database.get_all_deleted_containers()
print(users)
print(nodes)
print(images)
print(containers)
print(dels)
pdb.set_trace()
