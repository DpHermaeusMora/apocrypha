# What is Apocrypha?
**Apocrypha is a open source, automated builder to create an enterprise-level, bare-metal kubernetes cluster.**

# Prerequisities

* Ubuntu 22.04 
* AWS credentials (~/.aws/credentials)
* Secrets managed by AWS Secret manager
* Git SSH Key
* 1 console, 1 control plane, and at least 3 storage nodes named with storage-node and raw disk attached
* Minimum 8gb of static ram for each nodes

# Installation

## Create vm
* If you're using Hyper-V, make sure you have `External Switch` for static ip allocation and `Microsoft UEFI Certificate Authority` option has turned on
* Download ubuntu iso from [Ubuntu 22.04 live server](https://releases.ubuntu.com/jammy/ubuntu-22.04.5-live-server-amd64.iso)
* Duplicate /etc/cloud/cloud.cfg.d/user-data on iso. See with user-data on the project root
* Create vms with kernal parameter
```bash
ip=<ip:-192.168.0.15>::<gateway_ip:-192.168.0.1>:<subnet_mask:-255.255.255.0>::<nic:-eth0>:none:<dns:-1.1.1.1:8.8.8.8> hostname=<hostname:-my-storage-node-1> quiet autoinstall
```

## Setup dev environment
If all vm has created, you can set up k8s cluster with ansible. If ansible(and docker) does not installed yet, follow commands:
```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --user
python3 -m pip install --user ansible
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
ansible --version
sudo apt-get install docker.io
sudo usermod -aG docker "$USER"
newgrp docker
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.35.1/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
\. "$HOME/.nvm/nvm.sh"
nvm install 22 
```
(If you use ansible vscode extension, set `"ansible.ansible.path": "~/.local/bin/ansible"` for autocomplete.)

Then simply run `ansible-playbook site.yml -e env=dev -e role=cluster` in a project root for bootstrap k8s cluster.

## Argocd
* Get argocd initial password by `kubectl get secret argocd-initial-admin-secret -n argocd -o=jsonpath='{.data.password}' | base64 -d`
* Access to web UI by `kubectl port-forward svc/argocd-server -n argocd 30080:80`
* Login and change password

## Wireguard
* You must add port-forward from external port 51820 to {internal-ip}:51820. Internal ip must be specified in both `IPAddressPool` and annotation `metallb.io/loadBalancerIPs` of wireguard service.
* Prepare server key set by `wg genkey` and `echo {private key} | wg pubkey`
* Create Secret on your provider. I strongly recommned to use `AWS ParameterStore`, so that you can easily set configs like this:
`./ssm set /wireguard -e '{"LIST":[{"NAME":"foo","S_KEY":"..","S_PUBKEY":"..","S_NET":"172.16.16.0/24","S_PORT":51820,"C_PUBKEY":"..","C_NET":"172.16.100.0/24"}]}' -s`
* **All properties must be unique.**
* Update secret `wg-config`
* Client config might be like this: 
```
[Interface]
PrivateKey = ".."
Address = 172.16.100.0/24
DNS = 10.96.0.10, 8.8.8.8
MTU = 1280

[Peer]
PublicKey = ".."
AllowedIPs = 0.0.0.0/0
Endpoint = "..":51820
```

## ECK
* Get user elastic's password by `kubectl get secret -n eck-{env} es-es-elastic-user -o jsonpath='{.data.elastic}' | base64 -d`
* Login and change password

## Redis
* After redis cluster sts ready, you have to create cluster with command: `kubectl exec -it -n ".." redis-0 -- redis-cli --cluster create $(for i in {0..5}; do echo "redis-$i.redis-cluster-headless:6379"; done) --cluster-replicas 1 --cluster-yes`

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