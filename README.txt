This is the initial Python implementation of City Hall.

ABOUT

The intention is for this to be an Enterprise Settings Server, to allow users
to use this instead of keeping such settings in files or purpose-made tables.
City Hall is meant to be entirely behind the firewall and speaks REST to its
clients.



WHAT CITY HALL IS NOT

City Hall is not a key-value store and it is not distributed. The idea behind 
City Hall is have a product to centralize settings which will face business 
(behind the firewall), QA, and development.



INSTALL

1. Create and install all of the requirements

virtualenv env
source env/bin/activate
pip install -r requirements.txt

2. Configure

City Hall will needs to have configured a class which implements the abstract
class Db in lib.db.db.  The current options are:
  lib.db.memory.cityhall_db  - in memory, per instance database.  This is here
 		to set an example of what the DB interface needs to look like.
  lib.db.sqlite.sqlite_db - an sqlite database, this is so that it can easily
		be evaulatued, without needing to install or connect to a DB.



ENVIRONMENTS AND VALUES

City Hall supports key-value through paths and values, and it also
supports environments.  The idea behind this is to have the same 
code run on a local machine, dev environment, qa environment, and
production without needing to change any code, since the paths 
between all of these environments will be identical, although their
values will likely be different.  This has the benefit of 
offloading settings management to teams other than development.



GETTING STARTED

1. Create the virtual environment and install the requirements.txt
2. Run the server:
	python manage.py runserver 5000
3. Check to see that it is alive by going to:
		curl http://localhost:5000/api/info/
   this will return: 
  		{"Status": "Alive", "Database": "(In-Memory Db): Values: None, Authorizations: None"}
   Note here that:
   	 1) we are using an in-memory  database, so everything will be
   	gone on the next reset.  
   	 2) It has not been set up yet.
4. Create a default environment:
		curl http://localhost:5000/api/create_default/
    You can always ping that URL, if the default tables have 
    already been set up, it is a no-op.  If you go back to 
		curl http://localhost:5000/api/info/
    You will see that we now have data in the database.
5. The call to create_default has installed a default user named
   'cityhall' with no password, and a default environment named auto.
   It will also create a user named guest with no password with
   Read permissions for the auto environment.



API

The API calls in this guide will be written like this:
	POST	http://localhost:5000/api/auth/create/env/
	Auth-Token: [Authenticate Token]
	{"name": "dev"}
The first line is the verb and URL, the second line is the extra
headers that have to be passed in, the third line is the sample JSON
to follow along with the guide. The idea is to translate these to a
call from the program that will be using City Hall or, for the purposes
of this guide, a curl call from the command line:
	curl -X POST -H "Content-Type: application/json" -H "Auth-Token: [Authenticate Token]" -d '{"name": "dev"}' http://localhost:5000/api/auth/create/env/
	
	
	
API - AUTHORIZATION

Everything hanging off of http://localhost:5000/api/auth/
is related to users and user rights.  There is a simple scheme for 
rights:
	0) None - The user has neither read nor write
	1) Read - The user can read un-protected values
	2) Read Protect - The user can read un-protected values and history
	3) Write - The user can write values
	4) Grant - The user can grant rights to this environment

You will also need to hit here first, in order to get an authentication
token.  This is a token that will be included will all subsequent calls
to City Hall.  The reason for this token is to avoid authentication on
every transaction, the authentication for this session will be stored 
and retrieved without hitting the database.

Authenticate:
	POST	http://localhost:5000/api/auth/
	{"username": "cityhall", "passhash": ""}
Returns: {"Token": "PPeiSCshNpwFxAuJWUMshM", "Response": "Ok"}
	 
Create environment:
	POST	http://localhost:5000/api/auth/create/env/
	Auth-Token: PPeiSCshNpwFxAuJWUMshM
	{"name": "dev"}
Returns: {"Response": "Ok"}
This sets gives the current user Grant permissions on that environment

Create user:
	POST	http://localhost:5000/api/auth/create/user/
	Auth-Token: PPeiSCshNpwFxAuJWUMshM
	{"user": "alex", "passhash": ""}
Returns: {"Response": "Ok"}
This creates a user with None permissions on auto environment

Grant permissions:
	POST	http://localhost:5000/api/auth/grant/
	Auth-Token: PPeiSCshNpwFxAuJWUMshM
	{"env": "dev", "user": "alex", "rights": 1}
Returns: {"Response": "Ok"}



API - ENVIRONMENT

Everything hanging off of http://localhost:5000/api/env/
is related to getting and storing values or history for a particular
environment

Create a value:
	POST	http://localhost:5000/api/env/create/
	Auth-Token: PPeiSCshNpwFxAuJWUMshM
	{"env": "dev", "name": "/some_app", "value": ""}
Returns: {"Response": "Ok"}

Create a child value:
	POST	http://localhost:5000/api/env/create/
	Auth-Token: PPeiSCshNpwFxAuJWUMshM
	{"env": "dev", "name": "/some_app/value1", "value": "abc"}
Returns: {"Response": "Ok"}

Create an override child value:
	POST	http://localhost:5000/api/env/create/
	Auth-Token: PPeiSCshNpwFxAuJWUMshM
	{"env": "dev", "name": "/some_app/value1", "value": "def", "override": "cityhall"}
Returns: {"Response": "Ok"}

Get a value:
	GET		http://localhost:5000/api/env/view/dev/some_app/value1/
	Auth-Token: PPeiSCshNpwFxAuJWUMshM
Returns: {"Response": "Ok", "value": "def"}
	
	
	
API - GUEST USER

You can use GET to retrieve values without specifying an Auth-Token
headers, but an account named 'guest' must be created and be granted
permissions to that environment.

The guest account was already created in the GETTING STARTED section
so we first have to give it access to the dev environment
	POST	http://localhost:5000/api/auth/grant/
	Auth-Token: PPeiSCshNpwFxAuJWUMshM
	{"env": "dev", "user": "guest", "rights": 1}

Then, you should be able to call without specifying an Auth-Token:
	GET		http://localhost:5000/api/env/view/auto/some_app/value1
The call above will return: {"Response": "Ok", "value": "abc"}

Note here that the response at the same URL has returned two different
values.  When we used the cityhall authorization, City Hall preferred
the override that matched its name.  When we used guest, it defaulted
to the no override value.



API - ENVIRONMENT OTHER

These are here for extended functionality of City Hall.  For example,
all of these end points are used by the Viewer app, but they're not
meant to be part of the day-to-day usage of City Hall (the intent is to
use a graphical user interface to set/create values, and then consume
it using a library).

View children:
	GET		http://localhost:5000/api/env/view/dev/some_app/?viewchildren=true
	Auth-Token: PPeiSCshNpwFxAuJWUMshM
Returns: {
	"Response": "Ok", 
	"path": "/dev/some_app/", 
	"children": [
		{
			"override": "", 
			"path": "/dev/some_app/value1", 
			"name": "value1", 
			"value": "abc", 
			"id": 6
		},
		{
			"override": "cityhall", 
			"path": "/dev/some_app/value1", 
			"name": "value1", 
			"value": "def", 
			"id": 7
		},
	]}
	
View history:
	GET 	http://localhost:5000/api/env/view/auto/some_app/value1?override=cityhall&viewhistory=true
	Auth-Token: PPeiSCshNpwFxAuJWUMshM
Returns: {
	"Response": "Ok", 
	"History": [
		{
			"protect": 0, 
			"name": "value1", 
			"author": "cityhall", 
			"value": "val1", 
			"datetime": "2015-06-02T14:13:03", 
			"active": 1, 
			"id": 4
		}
	]