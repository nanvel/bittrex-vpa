# Bittrex volume-price analysis

Collect market history (closed buy and sell orders),
and try to detect support and resistance based on it (locate areas where large volumes are locked),
detect accumulation and distribution phases by observing money flow.

## Database

Alembic usage:
```bash
alembic revision --autogenerate -m <title>
alembic upgrade head
```

## Deploy

```bash
cd ansible && ansible-playbook deploy.yml -u root -i <inventory file> --vault-password-file <password file>
```
