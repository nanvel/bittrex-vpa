# Bittrex volume-price analysis

Collect market history (closed buy and sell orders),
and try to detect support and resistance based on it (locate areas where large volumes are locked),
detect accumulation and distribution phases by observing money flow.

## Installation

You can run it locally, or deploy to a server using yaml deploy script.

Python3.6 or higher is required.

Install requirements:
```
pip install -r requirements.txt
pip install -r requirements_dev.txt
```

You need a postresql database. One way to create it:

```bash
sudo su - postgres
postgres@local:~$ psql template1
template1=# CREATE USER vpa WITH PASSWORD 'vpa';
template1=# CREATE DATABASE vpa;
template1=# GRANT ALL PRIVILEGES ON DATABASE vpa to vpa;
template1=# \q

vim /etc/postgresql/<version>/main/pg_hba.conf
# add 'local   vpa     vpa                               password'
```

For creating table - use alembic upgrade. Make sure `sqlalchemy.url` looks good in `alembic.ini`.
Then run
```bash
alembic upgrade head
```

### Running locally

Make sure `vpa/settings.py` looks good.

```bash
python manage.py watch
```

In another console (for web server):
```bash
python manage.py server
```

### Deploy

`password file` you must create yourself and put a password in it.

Encrypt your domain name with:
```bash
ansible-vault --vault-password-file <password file> encrypt_string <some string>
```

And insert the result into variables.yaml.

`inventory file` must contain server addresses (see ansible documentation).
Access by ssh key must be setted up.

Deploy:
```bash
cd ansible && ansible-playbook deploy.yml -u root -i <inventory file> --vault-password-file <password file>
```
