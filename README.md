boby
========

Web interface for the package building and deployment tool.

Installation
============

To launch the webserver:

    $ cd boby
    $ mkvirtualenv boby
    $ # libevent install is required on OsX
    $ # can be installed through homebrew (recommended) or macports
    $ pip install --upgrade -r requirements.pip
    $ BOBY_SETTINGS=./config_vagrant.rc ./manage.py runserver
    
It can also run as a uwsgi app:

    $ BOBY_SETTINGS=./config_vagrant.rc uwsgi --socket 0.0.0.0:5000 --master --die-on-term --memory-report --virtualenv ~/.virtualenvs/boby --pythonpath /code/boby/boby/ --module boby.main --callable app

You will need to have an instance of Redis running as well and configured in the `config.rc` file.
By using `config_vagrant`, you will actually use the one in Bidasse/Vagrant VM.

The build machine needs to have installed `trebuchet`:

    $ git clone git@github.com:ops-hero/trebuchet.git
    $ cd trebuchet
    $ sudo python setup.py install
    $ trebuchet --version


Todo
====

* authentication (github oauth)
* websocket
* logs / error handling
* locking (not build the projects in // for 1 stack)
* integration with mise-a-feu
* status page for deployment, hosts
* replace meta api for stack
