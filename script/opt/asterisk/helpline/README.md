## Helpline Asterisk Configs

The helpline application requires these configs to integrate to Asterisk.
We use ODBC to connect to the backend database.

## Requirements

 * Asterisk 13+
 * unixODBC
 * odbc-postgresql - For PostgreSQL Connections

## Installation

Install package dependancies, Asterisk is not included as we assume it's already set up.

```
    sudo apt install odbc-postgresql
```

Clone the config directory.
We are placing them in the /opt/asterisk/ directory

```
    sudo mkdir /opt/asterisk/
    cd /opt/asterisk/
    git clone THIS_REPO.git
```

Add the following lines to the end of each of the corresponding files.

    /etc/asterisk/extensions.conf

    ADD 

```
    #include /opt/asterisk/helpline/app/exten.conf
```

    /etc/asterisk/sip.conf

    ADD 

```
    #include /opt/asterisk/helpline/app/sip.conf
```

    /etc/asterisk/func_odbc.conf

    ADD

```
    #include /opt/asterisk/helpline/app/func_odbc.conf
```

```
On

/etc/asterisk/queues.conf

ADD

#include /opt/asterisk/helpline/app/queues.conf
```


## Example odbc.ini config.

Below is an example odbc.ini configuration.

    /etc/odbc.ini

```
[helplineconn]
Driver      = PostgreSQL Unicode
Description = PostgreSQL Connection to Asterisk database
Database    = helpline
; This should match your helpline application database
Servername  = 127.0.0.1
; OR IP of your database server
User        = helplineuser
Password    = MYSUPERSECRETPASSWORD 
Port        = 5432
```


## Example res_odbc.conf config

Below is an example res_odbc.conf config to tell asterisk how to connect to your database.


```
[helpline]
enabled => yes
dsn => helplineconn
username => helplineuser
password => MYSUPERSECRETPASSWORD
pre-connect => yes
```

Restart asterisk

    sudo /etc/init.d/asterisk restart

Check to make sure odbc is working properly.

    sudo asterisk -x "odbc show"

The above command should give you the following output if configured correctly:

```

ODBC DSN Settings
-----------------

  Name:   helpline
  DSN:    helplineconn
    Last connection attempt: 1970-01-01 03:00:00
    Number of active connections: 1 (out of 1)

```

Also you can test ODBC by using the following command in your terminal application:

     isql -v helplineconn helplineuser MYSUPERSECRETPASSWORD


The above command should give you the following output:

```
+---------------------------------------+
| Connected!                            |
|                                       |
| sql-statement                         |
| help [tablename]                      |
| quit                                  |
|                                       |
+---------------------------------------+
SQL>
```

Once you've done this make sure you've created the appropriate services and hotdesks in Helpline.
