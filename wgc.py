#!/usr/bin/env python3

import argparse
import json
import subprocess
import ipaddress
import sys
import os
from typing import Optional

def get_interactive_input(prompt: str, default: str = None, required: bool = False) -> str:
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    while True:
        value = input(full_prompt).strip()
        
        if not value and default:
            return default
        elif not value and not required:
            return ""
        elif not value and required:
            print("This value is required. Please enter again.")
            continue
        else:
            return value

class WireguardHelper:
    def __init__(self, path: str, base_net: str, base_port: int, host: str, dns: str, mtu: int, allowed_ips: str):
        self.server_config_path = path
        self.base_net = base_net
        self.base_port = base_port
        self.dns = dns
        self.mtu = mtu
        self.allowed_ips = allowed_ips
        self.host = host
        if not os.path.exists(self.server_config_path):
            os.makedirs(os.path.dirname(self.server_config_path), exist_ok=True)
            open(self.server_config_path, 'w').write('{"LIST": []}')
        self.server_config = json.load(open(self.server_config_path))
        self.temp_allocated_net = None

    def interactive_add_config(self):
        server_key = subprocess.run(["wg", "genkey"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
        server_pubkey = subprocess.run(["wg", "pubkey"], input=server_key, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
        
        client_key = subprocess.run(["wg", "genkey"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
        client_pubkey = subprocess.run(["wg", "pubkey"], input=client_key, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
        
        config = {}
        config['NAME'] = get_interactive_input("Name", required=True)
        config['S_KEY'] = get_interactive_input("Server Key", server_key)
        config['S_PUBKEY'] = get_interactive_input("Server Pubkey", server_pubkey)
        config['S_NET'] = get_interactive_input("Server Network", self.get_available_net(self.base_net))
        config['S_PORT'] = get_interactive_input("Port", self.get_available_port(self.base_port))
        config['C_NET'] = get_interactive_input("Client Network", self.get_available_net(self.base_net))
        config['C_KEY'] = get_interactive_input("Client Key", client_key)
        config['C_PUBKEY'] = get_interactive_input("Client Pubkey", client_pubkey)
        
        return config

    def update_server_config(self, name: str):
        result = next(((i, x) for i, x in enumerate(self.server_config['LIST']) if x['NAME'] == name), (None, None))
        config_index, config = result
        
        if config is None:
            print(f"Error: Server config for {name} not found")
            sys.exit(1)
            
        config['S_KEY'] = get_interactive_input("Server Key", config['S_KEY'])
        config['S_PUBKEY'] = get_interactive_input("Server Pubkey", config['S_PUBKEY'])
        config['S_NET'] = get_interactive_input("Server Network", config['S_NET'])
        config['S_PORT'] = get_interactive_input("Port", config['S_PORT'])
        config['C_NET'] = get_interactive_input("Client Network", config['C_NET'])
        config['C_KEY'] = get_interactive_input("Client Key", config['C_KEY'])
        config['C_PUBKEY'] = get_interactive_input("Client Pubkey", config['C_PUBKEY'])
        
        self.server_config['LIST'][config_index] = config
        json.dump(self.server_config, open(self.server_config_path, 'w'), indent=4)
        
    def set_server_config(self, config: dict):
        self.server_config['LIST'].append(config)

        json.dump(self.server_config, open(self.server_config_path, 'w'), indent=4)

    def delete_server_config(self, name: str):
        self.server_config['LIST'] = [x for x in self.server_config['LIST'] if x['NAME'] != name]
        json.dump(self.server_config, open(self.server_config_path, 'w'), indent=4)

    def show_server_config(self):
        print(json.dumps(self.server_config, indent=4))

    def show_peers(self, name: str):
        config = next((x for x in self.server_config['LIST'] if x['NAME'] == name), None)
        if not config:
            print(f"Error: Server config for {name} not found")
            sys.exit(1)
        print(f"[Interface]\nPrivateKey = {config['C_KEY']}\nAddress = {config['C_NET']}\nDNS = {self.dns}\nMTU = {self.mtu}")
        print(f"[Peer]\nPublicKey = {config['S_PUBKEY']}\nAllowedIPs = {self.allowed_ips}\nEndpoint = {self.host}:{config['S_PORT']}\n")

    def get_available_net(self, base_net: str) -> str:
        allocated_nets = {x['S_NET']: 1 for x in self.server_config['LIST']} | {x['C_NET']: 1 for x in self.server_config['LIST']}
        if self.temp_allocated_net:
            allocated_nets[self.temp_allocated_net] = 1
        base_network = ipaddress.ip_network(base_net)
        for subnet in base_network.subnets(new_prefix=24):
            subnet_str = str(subnet)
            if subnet_str not in allocated_nets:
                self.temp_allocated_net = subnet_str
                return subnet_str
                
        raise ValueError(f"No available /24 network found in {base_net}")
    
    def get_available_port(self, base_port: int) -> int:
        allocated_ports = {x['S_PORT']: 1 for x in self.server_config['LIST']}
        for port in range(base_port, 65535):
            if port not in allocated_ports:
                return port
        raise ValueError("No available port found")

def main():
    default_path = os.path.expanduser("~/.ssh/apocrypha.wg.json")
    default_base_net = "172.16.0.0/16"
    default_base_port = 51820
    default_dns = "10.96.0.10, 8.8.8.8"
    default_mtu = 1500
    default_allowed_ips = "0.0.0.0/0"
    default_host = "our4000.iptime.org"

    parser = argparse.ArgumentParser(
        description="Wireguard Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage="wg [command] [options]"
    )
    parser.add_argument("-p", "--path", dest="path", type=str, required=False, default=default_path)
    parser.add_argument("--base-net", dest="base_net", type=str, required=False, default=default_base_net)
    parser.add_argument("--base-port", dest="base_port", type=int, required=False, default=default_base_port)
    parser.add_argument("--host", type=str, required=False, default=default_host)
    parser.add_argument("--dns", type=str, required=False, default=default_dns)
    parser.add_argument("--mtu", type=int, required=False, default=default_mtu)
    parser.add_argument("--allowed-ips", type=str, required=False, default=default_allowed_ips)
    

    command_parser = parser.add_subparsers(dest="command", help="Available commands")

    command_parser.add_parser("show", help="Show server config")
    command_parser.add_parser("add", help="Add both server and client config")

    del_parser = command_parser.add_parser("del", help="Delete server config")
    del_parser.add_argument("-n", "--name", dest="del_name", type=str, help="Name of the server to delete")

    update_parser = command_parser.add_parser("update", help="Update server config")
    update_parser.add_argument("-n", "--name", dest="update_name", type=str, help="Name of the server to update")

    showpeer_parser = command_parser.add_parser("showpeer", help="Show peers config")
    showpeer_parser.add_argument("-n", "--name", dest="showpeer_name", type=str, help="Name of the server to show peers")

    args = parser.parse_args()

    wg = WireguardHelper(path=args.path, base_net=args.base_net, base_port=args.base_port, host=args.host, dns=args.dns, mtu=args.mtu, allowed_ips=args.allowed_ips)

    try:
        if args.command == "add":
            config = wg.interactive_add_config()
            wg.set_server_config(config)
        elif args.command == "show":
            wg.show_server_config()
        elif args.command == "showpeer":
            if not args.showpeer_name:
                print("Error: -n, --name is required")
                sys.exit(1)
            wg.show_peers(args.showpeer_name)
        elif args.command == "del":
            if not args.del_name:
                print("Error: -n, --name is required")
                sys.exit(1)
            wg.delete_server_config(args.del_name)
        elif args.command == "update":
            if not args.update_name:
                print("Error: -n, --name is required")
                sys.exit(1)
            wg.update_server_config(args.update_name)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)

if __name__ == "__main__":
    main()