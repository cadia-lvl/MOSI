# M.O.S.I.
MOSI is a evaluation client made specifically for TTS evaluation. It supports Mean opinion score(MOS), AB and ABX tests, and can accommodate some needs for a SUS test. The development and testing for this platform has been done on Linux(Ubuntu 16 or later, reccomended choice) and on MACOS(with some modifications).

# Setup
* Other system requirements (installed via apt):
    * postgresql: `sudo apt install postgresql postgresql-contrib`
    * python-psycopg2: `sudo apt-get install -y python3-psycopg2`
    * libpq-dev: `sudo apt-get install -y libpq-dev`
    * libffi-dev: `sudo apt-get install -y libffi-dev`

* On ubuntu might have to run `sudo apt-get install python3-dev`
* Now, cd into MOSI, make a python virtual environment within the MOSI dir `python3.6 -m venv py36`
* Activate venv using `source py36/bin/activate`
* Conda venv is fine as well. Python 3.6 is good, the platform has been tested on Pthon 3.8 as well but using it might lead to some version conrtol and tinkering when installing the requirements. Should you run into any errors while installing requirements, it is usually due to some version mixup, easily fixable by changing versions of python or in requirements.txt.
* Install Python requirements using `pip3 install -r requirements.txt`
    * ffmpeg (or avconv)

* Create a Postgres database. Relevant parameters need to be supplied to the flask via the setting files at `settings/development.py` or `settings/production.py`.
* Spin up a simple development server using `./dev.sh`.
    * Use `SEMI_PROD=True` to use `avconc` instead of `ffmpeg`

# Creating a development database
Start by creating a databese and a user:

```
# Log in as postgres user
sudo -u postgres -i
# Create role for mosi and select password
createuser mosi --pwprompt
# Create mosi database with the new user as owner
createdb mosi --owner=mosi
```
Remember to change settings/development.py accordingly. Replace all the values in \<BRACKETS\> with the postgres information you created just now.
`SQLALCHEMY_DATABASE_URI = 'postgresql://<POSTGRES-USERNAME>:<POSTGRES-PWD>@localhost:5432/<DATABASENAME>'`

Finally run `python manage.py db upgrade`

To add defaults to the database run:

```
python manage.py add_default_roles
python manage.py add_default_configuration
```

Create a super user with `python manage.py add_user`


# Backing up & restoring
1. Create a new database.
    1. sudo su postgres
    2. psql
    3. CREATE DATABASE <name>;
    4. GRANT ALL PRIVILEGES ON DATABASE <name> TO <db_user>;

2. Create a database dump of the previous database
    1. su <mosi_linux_user>
    2. pg_dump <old_db_name> > <old_db_name>.sql

3. Migrate the schema to the new database
    1. In settings.<env_name>.py add <name> as the new database name
    2. run `python3 manage.py db upgrade`
    3. sudo su postgres
    4. try to restore from the backup with psql <name> < <old_db_name>.sql

4. If that didn't work the following is perhaps helpful
    1. Rename the migrations folder to e.g. `migrations_old`
    2. Recreate the new database by e.g. DROP DATABASE <name> and then create.
    3. Try to restore from the same backup as before

5. If that didn't work, try this
    1. Recreate a fresh database and run python3 manage.py db init and then run migrates to get schema updates on new database.
    2. Try creating a dump using `pg_dump -U <user> -Fc '<old_db_name>' > <old_db_name>.dump`
    3. Restore one table at a time using only data :`pg_restore -U <user> --data-only -d <new_db_name> -t <table> <old_db_name>.dump`
    4. Finally restore each sequence by first listing the sequences of the connected database with `\ds`
    5. For each table do SELECT max(id) from <table>;
    6. Then alter each sequence with ALTER SEQUENCE <sequence_name> RESTART WITH value+1;
