# 2017-fall-team-03
# Container as a Service

Reference:

    commands for creating mysql docker container: https://severalnines.com/blog/mysql-docker-building-container-image

    docker inspect <docker_name>

    network commands: https://docs.docker.com/engine/reference/commandline/network_connect/

    creating docker image with sshd: https://docs.docker.com/engine/examples/running_ssh_service/

    For creating login/signup page: https://www.youtube.com/watch?v=8aTnmsDMldY

Dependencies:
```
certifi==2017.11.5
chardet==3.0.4
click==6.7
dominate==2.3.1
Flask==0.12.2
Flask-Bootstrap==3.3.7.1
Flask-Login==0.4.0
Flask-SQLAlchemy==2.3.2
Flask-WTF==0.14.2
idna==2.6
itsdangerous==0.24
Jinja2==2.10
MarkupSafe==1.0
pbr==3.1.1
requests==2.18.4
six==1.11.0
SQLAlchemy==1.1.15
stevedore==1.27.1
urllib3==1.22
virtualenv==15.1.0
virtualenv-clone==0.2.6
virtualenvwrapper==4.8.2
visitor==0.1.3
Werkzeug==0.12.2
WTForms==2.1
```

# Run and execute: 
```
# (Optional) Install Virtualenv for separating your different python environments.
# More info here: https://virtualenv.pypa.io/en/latest/installation/
pip install virtualenv
# Create Virtual Environment
virtualenv cct
cd cct
# Activate virtual env
    # On windows do: `\path\to\env\Scripts\activate`
    # On Posix systems (e.g. Linux): `source bin/activate`
# Clone the repository
git clone https://github.ncsu.edu/engr-csc-547/2017-fall-team-03.git
cd 2017-fall-team-03
# Temporary: Untill this is merged in master. Checkout pritesh branch 
# git checkout pritesh
# Install all the dependencies.
pip install -r requirements.txt
# Run the app.
python app.py
```
Note: 
When run for the first time the app will create a `SQLAlchemy` db named `database.db`.
On subsequent runs the same database shall be used.
If you need a fresh start then delete the `database.db` file.

Source Code:
- `config.py` contains the configuration settings for the application.
- `container_health_report.py` Service that is to be run on each compute node.
- `lib/ContainerManager.py` Libraries functions for interacting with Docker containers.
- `lib/DatabaseManager.py` Library functions for interacting with Databases.
- `dockerFiles/*` This directory contains the DockerFiles to create various services.
- `python db_create.py` shall create the database schema in `database.db` file.
   If `database.db` exists, then it will be wiped out.
- `python db_insert.py` inserts default values in the `database.db` database.
- `models.py` contains the DB schema for the application.
- `app.py` contains the business logic of the app.
- `templates/*` contains the `html` files.
- `static/*` contains the `css` files.
