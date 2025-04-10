#!/usr/bin/env python3

# Recon Automation Drone
# This script automates the reconnaissance process using nmap and feroxbuster.
# It creates a tmux session with separate panes for each tool and runs them in parallel.
import subprocess
import argparse
import logging
import ipaddress
import time
import os
import re
from libtmux import Server

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_web_ports(nmap_output_file):
    """Parse nmap output to find web server ports"""
    web_ports = []
    if not os.path.exists(nmap_output_file):
        return web_ports
    
    try:
        with open(nmap_output_file, 'r') as f:
            content = f.read()
            
        # Check if scan is still running
        if "Nmap done:" not in content:
            return None  # Scan still in progress
            
        # Look for web servers
        # Pattern matches port numbers followed by "http" services
        port_pattern = r'(\d+)\/tcp\s+open\s+(http|https|ssl\/http|http-alt|https-alt)'
        http_matches = re.finditer(port_pattern, content, re.IGNORECASE)
        
        for match in http_matches:
            port = match.group(1)
            service = match.group(2)
            web_ports.append(port)
            
        # Also check for ports where the service name contains "http"
        service_pattern = r'(\d+)\/tcp\s+open\s+\w+\s+.*http'
        service_matches = re.finditer(service_pattern, content, re.IGNORECASE)
        
        for match in service_matches:
            port = match.group(1)
            if port not in web_ports:
                web_ports.append(port)
                
    except Exception as e:
        logging.error(f"Error parsing nmap output: {e}")
        
    return web_ports

def main():
    parser = argparse.ArgumentParser(description="Automate reconnaissance process.")
    parser.add_argument("-t", "--target", help="Target IP address or domain", required=True)
    args = parser.parse_args()

    target_ip = args.target
    nmap_output_file = f"nmap_{target_ip}.txt"

    # Validate the target IP address or domain
    try:
        ipaddress.ip_address(target_ip)
    except ValueError:
        logging.error("Invalid IP address or domain")
        return

    # Check if nmap, feroxbuster, and tmux are installed
    dependencies = ["nmap", "feroxbuster", "tmux"]
    for dependency in dependencies:
        try:
            subprocess.run([dependency, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            logging.error(f"{dependency} is not installed")
            return

    # Create a new tmux session
    try:
        server = Server()
        
        # Kill existing session if it exists
        try:
            existing_session = server.find_where({"session_name": "Drone"})
            if existing_session:
                existing_session.kill_session()
        except:
            pass
        
        # Create new session with attach=False
        session = server.new_session(session_name="Drone", attach=False, window_name="Recon")
        logging.info("New tmux session created")
        
        # Give tmux a moment to initialize
        time.sleep(0.5)
        
        # Get the initial window and pane for nmap
        window = session.attached_window
        nmap_pane = window.attached_pane
        nmap_pane.send_keys("clear")
        nmap_pane.send_keys(f"echo 'NMAP SCAN' && nmap -sC -sV -oN {nmap_output_file} {target_ip} -v -T4 --min-rate 1000")
        
        # Create a new pane for monitoring web servers
        ferox_pane = window.split_window(vertical=False)
        ferox_pane.send_keys("clear")
        ferox_pane.send_keys(f"echo 'Waiting for NMAP to discover web servers...'")
        
        # Set the layout to tiled for equal pane sizes
        window.select_layout("tiled")
        
        # Start the wait_and_scan script with proper environment variables
        ferox_pane.send_keys(f"export NMAP_OUTPUT_FILE='{nmap_output_file}'; export TARGET_IP='{target_ip}'; bash ./feroxscript.sh")
        
        # Attach to the tmux session
        logging.info("Attaching to tmux session...")
        os.system("tmux attach -t Drone")
        
    except Exception as e:
        logging.error(f"Error running reconnaissance process: {e}")

if __name__ == "__main__":
    main()