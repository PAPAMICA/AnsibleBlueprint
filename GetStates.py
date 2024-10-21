#!/usr/bin/env python3

import json
import logging
import subprocess
import os
from datetime import datetime

# Set up logging
logging.basicConfig(filename='server_info_collection.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command):
    """
    Execute a shell command and return its output.
    
    Args:
        command (str): The command to execute.
    
    Returns:
        str: The output of the command.
    """
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing command '{command}': {e}")
        return ""

def get_installed_packages():
    """
    Retrieve information about installed packages.
    
    Returns:
        list: A list of dictionaries containing package information.
    """
    logging.info("Retrieving installed packages information")
    packages = []
    try:
        output = run_command("dpkg-query -W -f='${Package}\t${Version}\n'")
        for line in output.split('\n'):
            if line:
                package, version = line.split('\t')
                packages.append({"name": package, "version": version})
    except Exception as e:
        logging.error(f"Error retrieving package information: {e}")
    return packages
def get_python_packages():
    """
    Retrieve information about installed Python packages.
    
    Returns:
        list: A list of dictionaries containing Python package information.
    """
    logging.info("Retrieving installed Python packages information")
    python_packages = []
    try:
        output = run_command("pip list --format=json")
        packages_data = json.loads(output)
        for package in packages_data:
            python_packages.append({
                "name": package["name"],
                "version": package["version"]
            })
    except Exception as e:
        logging.error(f"Error retrieving Python package information: {e}")
    return python_packages

def get_all_packages():
    """
    Retrieve information about all installed packages, including system and Python packages.
    
    Returns:
        dict: A dictionary containing lists of system and Python packages.
    """
    logging.info("Retrieving all installed packages information")
    return {
        "system_packages": get_installed_packages(),
        "python_packages": get_python_packages()
    }

def get_services():
    """
    Retrieve information about running services.
    
    Returns:
        list: A list of dictionaries containing service information.
    """
    logging.info("Retrieving services information")
    services = []
    try:
        output = run_command("systemctl list-units --type=service --state=running --no-pager --no-legend")
        for line in output.split('\n'):
            if line:
                service = line.split()[0]
                services.append({"name": service, "state": "running"})
    except Exception as e:
        logging.error(f"Error retrieving services information: {e}")
    return services

def get_network_config():
    """
    Retrieve network configuration information.
    
    Returns:
        dict: A dictionary containing network configuration details.
    """
    logging.info("Retrieving network configuration")
    network_config = {}
    try:
        network_config['interfaces'] = run_command("ip -j addr show")
        network_config['routing_table'] = run_command("ip -j route show")
        network_config['dns_servers'] = run_command("cat /etc/resolv.conf | grep nameserver")
    except Exception as e:
        logging.error(f"Error retrieving network configuration: {e}")
    return network_config

def get_users_and_groups():
    """
    Retrieve information about users and groups.
    
    Returns:
        dict: A dictionary containing user and group information.
    """
    logging.info("Retrieving users and groups information")
    users_and_groups = {}
    try:
        users_and_groups['users'] = run_command("cut -d: -f1,3 /etc/passwd")
        users_and_groups['groups'] = run_command("cut -d: -f1,3 /etc/group")
    except Exception as e:
        logging.error(f"Error retrieving users and groups information: {e}")
    return users_and_groups

def get_crontab():
    """
    Retrieve crontab information for all users.
    
    Returns:
        dict: A dictionary containing crontab information for each user.
    """
    logging.info("Retrieving crontab information")
    crontab = {}
    try:
        users = run_command("cut -d: -f1 /etc/passwd").split('\n')
        for user in users:
            user_crontab = run_command(f"crontab -l -u {user} 2>/dev/null")
            if user_crontab:
                crontab[user] = user_crontab
    except Exception as e:
        logging.error(f"Error retrieving crontab information: {e}")
    return crontab

def get_firewall_rules():
    """
    Retrieve firewall rules (iptables).
    
    Returns:
        str: The iptables rules as a string.
    """
    logging.info("Retrieving firewall rules")
    try:
        return run_command("iptables-save")
    except Exception as e:
        logging.error(f"Error retrieving firewall rules: {e}")
        return ""

def collect_server_info():
    """
    Collect all server information and return it as a dictionary.
    
    Returns:
        dict: A dictionary containing all collected server information.
    """
    server_info = {
        "timestamp": datetime.now().isoformat(),
        "hostname": run_command("hostname"),
        "os_version": run_command("cat /etc/os-release"),
        "kernel_version": run_command("uname -r"),
        "installed_packages": get_installed_packages(),
        "services": get_services(),
        "network_config": get_network_config(),
        "users_and_groups": get_users_and_groups(),
        "crontab": get_crontab(),
        "firewall_rules": get_firewall_rules()
    }
    return server_info

def main():
    """
    Main function to collect server information and save it to a JSON file.
    """
    logging.info("Starting server information collection")
    
    server_info = collect_server_info()
    
    output_file = f"server_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(server_info, f, indent=2)
        logging.info(f"Server information saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving server information to file: {e}")

if __name__ == "__main__":
    main()