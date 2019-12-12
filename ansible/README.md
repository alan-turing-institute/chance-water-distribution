# CHANCE Webapp Deployment

This directory contains an example ansible playbook to deploy the CHANCE webapp
on an Ubuntu 18.04 server. The app can then be connected to via http using an
NGINX reverse proxy.

## Security

Basic configuration of the server for security (for example restricting SSH
access and blocking unused ports) is beyond the scope of this playbook and
appropriate steps should be taken.

## Usage

Servers to deploy the webapp to should be in the 'appservers' group of your
Ansible inventory, for example
```ini
[appservers]
my-chance-app.com ansible_user=chance
```
The play can then be run with
```
ansible-playbook -i inventory chance.yml
```
The app should then be available on port 80 of your server
```
http://my-chance-app.com
```
