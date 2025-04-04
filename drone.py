#!/usr/bin/env python3
import subprocess
import argparse
import logging
import ipaddress
from libtmux import Server

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_open_ports(target_ip):
    """Run a fast nmap scan to get all open ports."""
    try:
        result = subprocess.run(
            ["nmap", "-p-", "--min-rate=1000", "-Pn", "-T4", target_ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        # Extract open ports from the nmap output
        open_ports = [
            line.split('/')[0]
            for line in result.stdout.splitlines()
            if line.startswith(tuple("0123456789"))
        ]
        return ",".join(open_ports)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running nmap to get open ports: {e}")
        return ""

def detect_web_servers(target_ip, open_ports):
    """Run a detailed nmap scan and check for web servers."""
    try:
        result = subprocess.run(
            ["nmap", "-p", open_ports, "-Pn", "-sC", "-sV", target_ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        # Check for web-related services in the nmap output
        web_servers = []
        for line in result.stdout.splitlines():
            if "http" in line.lower():  # Look for "http" in the service description
                port = line.split("/")[0]
                web_servers.append(port)
        return web_servers
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running nmap service scan: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Automate reconnaissance process.")
    parser.add_argument("-t", "--target", help="Target IP address or domain", required=True)
    args = parser.parse_args()

    target_ip = args.target

    # Validate the target IP address or domain
    try:
        ipaddress.ip_address(target_ip)
    except ValueError:
        logging.error("Invalid IP address or domain")
        return

    # Check if required tools are installed
    dependencies = ["nmap", "feroxbuster", "whatweb", "nikto"]
    for dependency in dependencies:
        try:
            subprocess.run([dependency, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            logging.error(f"{dependency} is not installed or not working correctly")
            return

    # Get open ports using a fast nmap scan
    logging.info("Running a fast nmap scan to identify open ports...")
    open_ports = get_open_ports(target_ip)
    if not open_ports:
        logging.error("No open ports detected. Exiting...")
        return
    logging.info(f"Open ports detected: {open_ports}")

    # Detect web servers from the detailed nmap scan
    logging.info("Running a detailed nmap scan to detect web servers...")
    web_servers = detect_web_servers(target_ip, open_ports)
    if not web_servers:
        logging.info("No web servers detected. Skipping web-related tools.")
    else:
        logging.info(f"Web servers detected on ports: {', '.join(web_servers)}")

    # Create a new tmux session or attach to an existing one
    try:
        server = Server()
        session_name = "recon"

        # Check if a session with the same name already exists
        if server.has_session(session_name):
            logging.info(f"Session {session_name} already exists. Attaching to it...")
            session = server.find_where({"session_name": session_name})
        else:
            # Create a new session
            session = server.new_session(session_name, attach=False)

        # Use the default window (index 0)
        window = session.attached_window

        # Send the detailed nmap command to the first pane
        pane1 = window.select_pane(0)
        pane1.send_keys(f"nmap -p{open_ports} -Pn -sC -sV -oN nmap_{target_ip}.txt {target_ip}")

        # Run web-related tools only if web servers are detected
        if web_servers:
            # Split the window horizontally for feroxbuster
            pane2 = window.split_window(attach=False)
            pane2.send_keys(f"feroxbuster -u http://{target_ip}:{web_servers[0]} -x txt,html,php -o feroxbuster_{target_ip}.txt")

            # Split the window vertically for whatweb
            pane3 = window.split_window(vertical=True, attach=False)
            pane3.send_keys(f"whatweb http://{target_ip}:{web_servers[0]} > whatweb_{target_ip}.txt")

            # Split the window vertically for nikto
            pane4 = window.split_window(vertical=True, attach=False)
            pane4.send_keys(f"nikto -h http://{target_ip}:{web_servers[0]} -o nikto_{target_ip}.txt")
        else:
            logging.info("No web servers detected. Skipping feroxbuster, whatweb, and nikto.")

        # Attach to the session
        session.attach()

        logging.info("Reconnaissance process started and session attached")
    except Exception as e:
        logging.error(f"Error running reconnaissance process: {e}")

if __name__ == "__main__":
    main()