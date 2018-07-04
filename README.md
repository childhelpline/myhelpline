# MyHelpline

MyHelpline is a communication framework for support call centers.
The goal is simple, to help users easily communicate to support agents.

Being a communication framework we have focused heavily on the voice and messaging.
Currently the application integrates with Asterisk the opensource PBX and hardware PBX such as GOIP and Yeastar MyPBX.
Support for other IP PBX Software such as Freeswitch is also on the pipe line.

The name is as random as it can get. "MyPBX" might have inspired some of the naming, however inadvertently.

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
    sudo apt install libmysqlclient-dev
    sudo apt install npm
    sudo apt install virtualenv
    sudo npm install -g bower
```

Install MySQL Server:

```
    sudo apt install mysql-server
```

Set password for MySQL root user as "root".

After you install nodejs you might want to run the following command:
Not required in Ubuntu 18.04 +

```
    ln -s /usr/bin/nodejs /usr/bin/node
```

```
    $ npm install -g bower
```

### Asterisk
On /etc/asterisk/manager.conf set command permission for read and write, example:

```
    [panel]
    secret = my_super_secret_password
    read = command
    write = command,originate,call,agent
```

#### AMI Options
    * _originate_ for spy, whisper and barge.
    * _call_ for hanging up calls.
    * _agent_ remove and add agents to and from the queues.

##  3. Go and prepair environment
 ```
  cd panel
  cp samples/config.ini-dist config.ini
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

## 4.- Translations
 ```
  python manage.py compilemessages
 ```


## 5.- Run and relax
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

Happy coding :)
