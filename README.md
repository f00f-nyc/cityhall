# CITYHALL [![Build Status](https://travis-ci.org/f00f-nyc/cityhall.svg?branch=master)](https://travis-ci.org/f00f-nyc/cityhall)

This is the v1 Python implementation of City Hall Enterprise Settings Server.

## ABOUT

This project is written in Python 3.8, and uses Django 3.0

The intention is for this to be an Enterprise Settings Server, to allow users
to use this instead of keeping such settings in files or purpose-made tables.
City Hall is meant to be entirely behind the firewall and speaks REST to its
clients.



## WHAT IS CITY HALL

City Hall is a stack-agnostic, light weight, settings server. The data is 
organized into environments, and then within those environments into a 
hierarchy (folders, value defaults, and  value overrides), to be used via their
path within an environment. City Hall also supports a simple permission system, 
making it possible to put sensitive data next to global, or not worry about 
having data modified by unauthorized users. Lastly, City Hall provides an 
audit trail for everything.

The main benefit here is offloading settings management to teams other than
development.  City Hall can be easily run on a dedicated server and has 
MIT-license libraries in many major languages/repos (pypi, nuget, npm, etc).

For more information, please checkout our [homepage](http://digitalborderlands.com/cityhall/)


## WHAT CITY HALL IS NOT

City Hall is not a key-value store and it is not distributed. The idea behind 
City Hall is have a product to centralize settings which will face business 
(behind the firewall), QA, and development.



## USING CITY HALL

For the purpose of this section, suppose we are working on an internal 
application, which needs to store the number of concurrent users. Usually, 
this would get a well-known identifier, and be stored in a settings file, 
then referenced in the code using that specific string.

In our example, we would create a environment (name it "dev") in City Hall, 
then create a folder for our app (name it "app1"), then make a value under that
folder named "num_users".  Now, when we need to use the value, analogous to
getting it from a settings file, we will use "/app1/num_users".  

Note here that the environment is not specified. City Hall connections are set
up in such a way that a user is meant to be connected to a particular
environment, by default.

Once development is done, other users also connecting to dev will begin to rely
on that value, so the user who wants to try out new things needs only make an 
override named for his user name. The code remains the same, the value is still
identified only via "/app1/num_users".

Once development is done, that setting needs to be QA'd. Different values have
to be tested, and while it would be possible to use the "dev" environment with
overrides for the qa users/machines, the accepted workflow is to create a "qa"
environment and have the qa users/machines connect to it.  Dev continues its
work without needing to worry about interfering with QA, and vice-versa. Again,
the code does not change, the setting is identified using "/app1/num_users".

Once QA is done, the process may be repeated again for UAT, or stress testing,
or others. Finally, the code is moved to production, and that setting is deemed
sensitive.  The value can be set to read only, so that dev is able to see what
the settings in production are, when they were changed, and by whom.

For more, please see GETTING.STARTED.txt


## DOCKER

You can run City Hall on docker, and there's a default image you can use:

    $ docker pull digitalborderlands/cityhall
    $ docker run -dp 8000:8000 digitalborderlands/cityhall

This will run it as a basic python server on port 8000. For a more robust
implementation, you can check out the [runon/docker](https://github.com/f00f-nyc/cityhall/tree/runon/docker) branch.
Using that branch, you will be able to run:

    $ docker-compose build && docker-compose up -d
    
And that will put up a nginx webserver, a Python 3.8 app server, a Postgres
database, and a Redis cache.

For either one of these, upon start up, use username cityhall with no 
password to check it out.

## LICENSE

  City Hall source files are made available under the terms of the GNU Affero General Public License (AGPL).
