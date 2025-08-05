#!/usr/bin/env python3

import argparse
import json
import profile
import sys
from typing import Any, Dict, List, Optional, Union

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class SSMHelper:
    def __init__(self, region_name: str, profile_name: str):
        try:
            self.ssm = boto3.Session(profile_name=profile_name).client('ssm', region_name=region_name)
        except NoCredentialsError:
            print("Error: AWS credentials not    found. Please configure AWS CLI.")
            sys.exit(1)
    
    def get_parameter(self, name: str) -> str:
        try:
            response = self.ssm.get_parameter(Name=name, WithDecryption=True)
            param = response['Parameter']
            
            # Show [SECRET] prefix for SecureString parameters
            if param['Type'] == 'SecureString':
                return f"[SECRET] {param['Value']}"
            else:
                return param['Value']
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ParameterNotFound':
                print(f"Error: Parameter '{name}' not found")
            elif error_code == 'AccessDenied':
                print(f"Error: Access denied to parameter '{name}'")
            else:
                print(f"Error: {e.response['Error']['Message']}")
            sys.exit(1)
    
    def set_parameter(self, name: str, value: Optional[str] = None, 
                     entries: Optional[List[str]] = None, 
                     is_secret: bool = False) -> None:
        try:
            if entries:
                # JSON mode: merge entries with existing value
                final_value = self._build_json_value(name, entries)
            elif value is not None:
                # Simple mode: use provided value
                final_value = value
            else:
                print("Error: Either value or entries must be provided")
                sys.exit(1)
            
            param_type = 'SecureString' if is_secret else 'String'
            
            self.ssm.put_parameter(
                Name=name,
                Value=final_value,
                Type=param_type,
                Overwrite=True
            )
            
            print(f"Parameter '{name}' updated successfully")
            
        except ClientError as e:
            print(f"Error: {e.response['Error']['Message']}")
            sys.exit(1)
    
    def delete_parameter(self, name: str, delete_keys: Optional[List[str]] = None) -> None:
        try:
            if delete_keys:
                # Partial deletion: remove specific keys from JSON
                self._delete_json_keys(name, delete_keys)
            else:
                # Complete deletion
                self.ssm.delete_parameter(Name=name)
                print(f"Parameter '{name}' deleted successfully")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ParameterNotFound':
                print(f"Error: Parameter '{name}' not found")
            else:
                print(f"Error: {e.response['Error']['Message']}")
            sys.exit(1)
    
    def list_parameters(self, path: str) -> None:
        try:
            if not path.startswith('/'):
                path = '/' + path
            
            paginator = self.ssm.get_paginator('get_parameters_by_path')
            
            parameters = []
            for page in paginator.paginate(
                Path=path,
                Recursive=True,
                WithDecryption=False
            ):
                parameters.extend(page['Parameters'])
            
            if not parameters:
                print(f"No parameters found in path '{path}'")
                return
            
            print(f"{'Name':<50} {'Type':<15}")
            print("-" * 65)
            
            for param in parameters:
                print(f"{param['Name']:<50} {param['Type']:<15}")
                
        except ClientError as e:
            print(f"Error: {e.response['Error']['Message']}")
            sys.exit(1)
    
    def _build_json_value(self, name: str, entries: List[str]) -> str:
        # Get existing value
        base_data = {}
        try:
            response = self.ssm.get_parameter(Name=name, WithDecryption=True)
            existing_value = response['Parameter']['Value']
            
            # Try to parse existing value as JSON
            try:
                base_data = json.loads(existing_value)
            except json.JSONDecodeError:
                print("Warning: Existing value is not valid JSON, starting with empty object")
                
        except ClientError as e:
            if e.response['Error']['Code'] != 'ParameterNotFound':
                raise
            # Parameter doesn't exist, start with empty object
        
        # Parse and merge entries
        for entry in entries:
            if '=' not in entry:
                print(f"Error: Invalid entry format '{entry}'. Use key=value")
                sys.exit(1)
            
            key, value = entry.split('=', 1)
            
            # Try to parse value as JSON, otherwise treat as string
            try:
                base_data[key] = json.loads(value)
            except json.JSONDecodeError:
                base_data[key] = value
        
        return json.dumps(base_data, separators=(',', ':'))
    
    def _delete_json_keys(self, name: str, delete_keys: List[str]) -> None:
        # Get existing parameter
        response = self.ssm.get_parameter(Name=name, WithDecryption=True)
        param = response['Parameter']
        
        # Parse JSON
        try:
            data = json.loads(param['Value'])
        except json.JSONDecodeError:
            print("Error: Existing value is not valid JSON")
            sys.exit(1)
        
        # Delete specified keys
        for key in delete_keys:
            if key in data:
                del data[key]
                print(f"Deleted key '{key}' from parameter '{name}'")
            else:
                print(f"Warning: Key '{key}' not found in parameter '{name}'")
        
        # Update parameter
        new_value = json.dumps(data, separators=(',', ':'))
        self.ssm.put_parameter(
            Name=name,
            Value=new_value,
            Type=param['Type'],
            Overwrite=True
        )


def main():
    parser = argparse.ArgumentParser(
        description='AWS SSM Parameter Store Helper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage='ssm [command] [options]'
    )
    
    parser.add_argument('--region', help='AWS region name', required=False, default='ap-northeast-2')
    parser.add_argument('--profile', help='AWS profile name', required=False, default='default')
    
    command_parser = parser.add_subparsers(dest='command', help='Available commands')
    
    # Get command
    get_parser = command_parser.add_parser('get', help='Get parameter value')
    get_parser.add_argument('name', help='Parameter name')
    
    # Set command
    set_parser = command_parser.add_parser('set', help='Set parameter value')
    set_parser.add_argument('name', help='Parameter name')
    set_parser.add_argument('value', nargs='?', help='Parameter value (simple mode)')
    set_parser.add_argument('-e', '--entry', action='append', dest='entries',
                           help='Add key=value pair (JSON mode)', metavar='KEY=VALUE')
    set_parser.add_argument('-s', '--secret', action='store_true',
                           help='Store as SecureString (encrypted)')
    
    # Delete command
    del_parser = command_parser.add_parser('del', help='Delete parameter')
    del_parser.add_argument('name', help='Parameter name')
    del_parser.add_argument('-e', '--entry', action='append', dest='entries',
                           help='Delete specific key from JSON parameter', metavar='KEY')
    
    # List command
    list_parser = command_parser.add_parser('list', help='List parameters')
    list_parser.add_argument('path', help='Parameter path (e.g., /app/database/)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize SSM helper
    ssm = SSMHelper(region_name=args.region, profile_name=args.profile)
    
    # Execute command
    try:
        if args.command == 'get':
            result = ssm.get_parameter(args.name)
            print(result)
            
        elif args.command == 'set':
            if args.entries and args.value:
                print("Error: Cannot use both value and entries. Choose simple or JSON mode.")
                sys.exit(1)
            elif not args.entries and not args.value:
                print("Error: Either value or entries must be provided")
                sys.exit(1)
                
            ssm.set_parameter(args.name, args.value, args.entries, args.secret)
            
        elif args.command == 'del':
            ssm.delete_parameter(args.name, args.entries)
            
        elif args.command == 'list':
            ssm.list_parameters(args.path)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)


if __name__ == '__main__':
    main()