This is the initial Python implementation of City Hall.

ABOUT

The intention is for this to be an Enterprise Settings Server, to allow users
to use this instead of keeping such settings in files or purpose-made tables.
City Hall is meant to be entirely behind the firewall and speaks REST to its
clients.

USES 



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

3. Run

The first thing after you set it up is to create a default enviroment.
 
