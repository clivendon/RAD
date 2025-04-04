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

        # Send the fast nmap scan command to the first pane
        pane1 = window.select_pane(0)
        pane1.send_keys(f"nmap -p- --min-rate=1000 -Pn -T4 -oN nmap_fast_{target_ip}.txt {target_ip}")

        # Wait for the fast nmap scan to complete
        pane1.send_keys(f"while [ ! -f nmap_fast_{target_ip}.txt ]; do sleep 1; done"))
        pane1.send_keys(f"grep -oP '\\d+/open' nmap_fast_{target_ip}.txt | cut -d'/' -f1 > open_ports.txt")

        # Wait for the open_ports.txt file to be created        # Wait for the open_ports.txt file to be created
        pane1.send_keys("while [ ! -f open_ports.txt ]; do sleep 1; done")]; do sleep 1; done")

        # Run the detailed nmap scan in the same pane        # Run the detailed nmap scan in the same pane
        pane1.send_keys(f"nmap -p $(cat open_ports.txt) -Pn -sC -sV -oN nmap_detailed_{target_ip}.txt {target_ip}")-sV -oN nmap_detailed_{target_ip}.txt {target_ip}")

        # Wait for the detailed nmap scan to completehe detailed nmap scan to complete
        pane1.send_keys(f"while [ ! -f nmap_detailed_{target_ip}.txt ]; do sleep 1; done")eys(f"while [ ! -f nmap_detailed_{target_ip}.txt ]; do sleep 1; done")

        # Check for HTTP servers in the detailed nmap outputt
        pane1.send_keys(f"grep -qi 'http' nmap_detailed_{target_ip}.txt && touch http_detected.txt")ed_{target_ip}.txt && touch http_detected.txt")

        # Wait for the HTTP detection result        # Wait for the HTTP detection result
        pane1.send_keys("while [ ! -f http_detected.txt ]; do sleep 1; done")xt ]; do sleep 1; done")

        # Run web-related tools if HTTP servers are detected
        pane2 = None        pane2 = None
        pane3 = None
        pane4 = None
        pane1.send_keys("if [ -f http_detected.txt ]; then exit 0; else exit 1; fi")
        if pane1.send_keys("test -f http_detected.txt"):ne1.send_keys("test -f http_detected.txt"):
            # Split the window horizontally for feroxbuster
            pane2 = window.split_window(attach=False)            pane2 = window.split_window(attach=False)
            pane2.send_keys(f"feroxbuster -u http://{target_ip} -x txt,html,php -o feroxbuster_{target_ip}.txt")eroxbuster -u http://{target_ip} -x txt,html,php -o feroxbuster_{target_ip}.txt")

            # Split the window vertically for whatweb            # Split the window vertically for whatweb
            pane3 = window.split_window(vertical=True, attach=False)
            pane3.send_keys(f"whatweb http://{target_ip} > whatweb_{target_ip}.txt")s(f"whatweb http://{target_ip} > whatweb_{target_ip}.txt")

            # Split the window vertically for nikto            # Split the window vertically for nikto
            pane4 = window.split_window(vertical=True, attach=False).split_window(vertical=True, attach=False)
            pane4.send_keys(f"nikto -h http://{target_ip} -o nikto_{target_ip}.txt")  pane4.send_keys(f"nikto -h http://{target_ip} -o nikto_{target_ip}.txt")












    main()if __name__ == "__main__":        logging.error(f"Error running reconnaissance process: {e}")    except Exception as e:        logging.info("Reconnaissance process started and session attached")        session.attach()        # Attach to the session            logging.info("No web servers detected. Skipping feroxbuster, whatweb, and nikto.")        else:        else:
            logging.info("No web servers detected. Skipping feroxbuster, whatweb, and nikto.")

        # Attach to the session
        session.attach()

        logging.info("Reconnaissance process started and session attached")
    except Exception as e:
        logging.error(f"Error running reconnaissance process: {e}")

if __name__ == "__main__":
    main()