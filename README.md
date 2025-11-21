# JO_24

## Requirements

This project uses Python Django to run.
You need to have at least Python 3.11 to run this server.
For the Database, we use MySQL.

## Environment

First (optional but recommended), prepare a virtual environment:

Change to the project root directory and run:
```
python -m venv .env
source .venv/bin/activate
```

Install project dependencies:
```
pip install -r requirements.txt
```

## Prepare Database

MySQL has been installed previously, so you can now initiate the creation of your DATABASES.
If not already done, you can create a user in MySQL by using your computer's terminal :

```
mysql -u root -p
```
Then you can create the DB :

```
CREATE DATABASE jo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'jo_user'@'localhost' IDENTIFIED BY 'motdepassefort';
GRANT ALL PRIVILEGES ON jo_db.* TO 'jo_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```
Change the information as you see fit and then configure in 'settings.py' the DATABASES part with your datas. 
You can also create an environment variable for your database connection data.
If you do so, you will need to install the python library at the root racine of the project :

```
pip install python-dotenv
```

Change to the _olympic_project/_ directory.

Create an .env file and enter your database login information.

Then generate a secure SECRET_KEY
```
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
You can now add your key for DJANGO_SECRET_KEY in your .env file

Verify the connexion with your database.

Run the migrations :
```
python manage.py makemigrations
python manage.py migrate
```

Generate test offers (demo with script) :
```
python manage.py seed_offers --events"Natation,Athlétisme,Gymnastique"
```

If needed, create a superuser with your credentials if you want to access the administration space :
```
python manage.py createsuperuser
```

By default : 
    admin_user : jose
    password : 1234jose

## Run the Server

```
python manage.py runserver
```

By default, the website is available at http://127.0.0.1:8000.

Link to the deployed app with Heroku :

https://jo24-tickets-jose-bace97e7a3b4.herokuapp.com/

## Tests coverage

Installation if needed :

```
pip install coverage
```

In order to access the coverage : 

```
coverage run 
-- source=olympic_tickets,tickets \
manage.py test -- settings:olympics_tickets.settings_test --keedb -v 2
```

To generate the html file of the current coverage :
```
coverage html
open htmlcov/index.html
```
Actual coverage at 80%
©Author : Emmanuel Di Nicola