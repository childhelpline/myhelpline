# MyHelpline

MyHelpline is a communication framework for support call centers.

[![Build Status](https://travis-ci.com/Kirembu/myhelpline.svg?branch=master)](https://travis-ci.com/Kirembu/myhelpline)
[![Coverage Status](https://coveralls.io/repos/github/Kirembu/myhelpline/badge.svg?branch=master)](https://coveralls.io/github/Kirembu/myhelpline?branch=master)
[![Documentation Status](https://readthedocs.org/projects/myhelpline/badge/?version=latest)](https://myhelpline.readthedocs.io/en/latest/?badge=latest)


## Requirements

 * Python 2.7
 * [Django](http://djangoproject.com/) 1.10+
 * [Asterisk](http://www.asterisk.org) 1.4+ and enabled manager
 * Redis >= 2.6.0
 * RabbitMQ
 * Nginx
 * PostgreSQL

## Technology Platform
 * Nginx
 * Python
 * Linux (Ubuntu)
 * PostgreSQL
 * Asterisk with AMI enabled.
 * RapidPRO

## Installation

Install package dependencies.

```
    sudo apt install python-dev
    sudo apt install npm
    sudo apt install virtualenv
    sudo npm install -g bower
    sudo apt install gettext
    sudo apt install postgresql postgresql-contrib
    sudo apt install python-gdal
    sudo apt install libmemcached-dev
    sudo apt-get install libz-dev
    sudo apt-get install postgis
```

To bulk install the requirements in Ubuntu run:

    ./script/install/ubuntu



After you install nodejs you might want to run the following command:
Not required in Ubuntu 18.04 +

```
    ln -s /usr/bin/nodejs /usr/bin/node
```

```
    $ npm install -g bower
```


## Database setup

### In the base OS

Replace username and db name accordingly.

.. code-block:: sh

    sudo su postgres -c "psql -c \"CREATE USER helplineuser WITH PASSWORD 'helplinepasswd';\""
    sudo su postgres -c "psql -c \"CREATE DATABASE helpline OWNER helplineuser;\""
    sudo su postgres -c "psql -d helpline -c \"CREATE EXTENSION IF NOT EXISTS postgis;\""
    sudo su postgres -c "psql -d helpline -c \"CREATE EXTENSION IF NOT EXISTS postgis_topology;\""
    sudo su postgres -c "psql -d helpline -c \"ALTER USER helplineuser WITH superuser;\""



##  Prepair environment

 go to project directory
 ```
  git clone https://github.com/childhelpline/myhelpline.git
  cd myhelpline
  cp helpline/config.ini-dist helpline/config.ini
  cp myhelpline/localsettings.py-sample myhelpline/localsettings.py
 ```
  Edit config.ini file with Manager Asterisk parameters

Create a virtual environment for the application.

```
    virtualenv ~/.env/
```

Activate virtual environment:

```
    source ~/.env/bin/activate
```

Install requirements:

```
    pip install -r requirements.txt
```

## Translations
 ```
  python manage.py compilemessages
 ```

## Migrations 
Make sure PostgreSQl is running and the cridentials for the  database are available in your "myhelpline/localsettings.py" 
```
python manage.py makemigrations
python manage.py migrate
   ```
   
## Load initial default data using fixtures

Use django fixtures we are able to load the initial default data that make setup easier.
This data includes "Hotdesks", which are a list of Soft Phone extension that can be used.
Also, we include a default service to help you get started.

```
python manage.py loaddata helpline
```


## Install components using bower
 ```
 python manage.py bower install

 ```
if running as root
```
bower install --allow-root
```
## Create User
 Run the following command and follow the prompt
  ```
  python manage.py createsuperuser
  ```
 
## Run webserver
 ```
    python manage.py runserver 0.0.0.0:8000
 ```

Go to url of the machine http://IP:8000


## How to contribute

 * Fork the project
 * Create a feature branch (git checkout -b my-feature)
 * Add your files changed (git add file_change1 file_change2, etc..)
 * Commit your changes (git commit -m "add my feature")
 * Push to the branch (git push origin my-feature)
 * Create a pull request
