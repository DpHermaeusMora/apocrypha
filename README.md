# Prerequisities

* Ubuntu 22.04 
* AWS Credentials has permissions for assumeRole: ssm:parameterstore, s3, cloudfront, route53, sqs, ecr
* 1 control plane node and at least 3 storage nodes with name containing `storage-node` and raw disk attached
* Minimum 8gb of static ram for each nodes

# Installation

## Create vm (Hyper-V)
* Make sure you have `External Switch` for static ip allocation and option `Microsoft UEFI Certificate Authority` is checked.
* Download ubuntu iso from [Ubuntu 22.04 live server](https://releases.ubuntu.com/jammy/ubuntu-22.04.5-live-server-amd64.iso)
* Copy `user-data` into /etc/cloud/cloud.cfg.d/user-data of iso
* Create vms with kernal parameter
```bash
ip=<ip:-192.168.0.15>::<gateway_ip:-192.168.0.1>:<subnet_mask:-255.255.255.0>::<nic:-eth0>:none:<dns:-1.1.1.1:8.8.8.8> hostname=<hostname:-my-storage-node-1> quiet autoinstall
```

## Setup dev environment
* If all vm has created, you can set up k8s cluster with ansible. If ansible(and docker) does not installed yet, follow commands:
```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --user
python3 -m pip install --user ansible
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
echo 'alias play="ansible-playbook"' >> ~/.bashrc
source ~/.bashrc
```
(If you use ansible vscode extension, set `"ansible.ansible.path": "~/.local/bin/ansible"` for autocomplete)
* Then simply run `play site.yml -e env=dev -e role=cluster` in a project root for bootstrap the k8s cluster.
* and run `play site.yml -e env=dev -e role=console` for bootstrap the console.

## Argocd
* Get argocd initial password by `kubectl get secret argocd-initial-admin-secret -n argocd -o=jsonpath='{.data.password}' | base64 -d`
* Access to web UI by `kubectl port-forward svc/argocd-server -n argocd 30080:80`
* Login and change password

## Wireguard
* Configure wireguard tunnel by `./wgc.py add`
* Set parameter by `./ssm.py set <SECRET_NAME> "$(./wgc.py show)" -s`
* Update secret name of `/roles/app/files/wireguard/config.yaml`
* Configure the wireguard peer. you could copy the configuration from `./wgc.py --host <YOUR_HOST> showpeer -n <PEER_NAME>`

## ECK
* Get user elastic's password by `kubectl get secret -n eck-{env} es-es-elastic-user -o jsonpath='{.data.elastic}' | base64 -d`
* Login and change password

## Redis
* After redis cluster sts ready, you have to create cluster with command: `kubectl exec -it -n <REDIS_NAMESPACE> redis-0 -- redis-cli --cluster create $(for i in {0..5}; do echo "redis-$i.redis-cluster-headless:6379"; done) --cluster-replicas 1 --cluster-yes`

## Naming Convention

* For file/dir, use `snake_case`
* For variables, use `camelCase`
* For classes/classes file, use `PascalCase`
* For environment variables, use `UPPER_SNAKE_CASE`
* For resource, use `kebab-case` and `{env}-{kind}-{domain}` fomat 
* For domain, use `kebab-case` and `{kind}-{env}-{domain}` fomat 

## Troubleshooting

#### callico unauthorized

This error happens usually at re-boot node. If you see an error like below:

```
Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox "fc93b9a5d7965c09414d707654cdb9e1b14ef0b10e91ab7c9e730cbe18ed1cd7": plugin type="calico" failed (add): error getting ClusterInformation: connection is unauthorized: Unauthorized
```

run 
```
k delete pod -l k8s-app=calico-node -n kube-system
```
