#!/bin/bash
# filepath: /home/clive/python/RAD/feroxscript.sh

# Properly access environment variables
echo "Starting feroxscript with NMAP_OUTPUT_FILE=$NMAP_OUTPUT_FILE and TARGET_IP=$TARGET_IP"

while true; do
  echo "Checking for web servers in $NMAP_OUTPUT_FILE..."
  
  # Check if file exists first
  if [ ! -f "$NMAP_OUTPUT_FILE" ]; then
    echo "Waiting for nmap output file to be created..."
    sleep 5
    continue
  fi
  
  # Debug - show what's in the file
  echo "Contents of nmap output file:"
  cat "$NMAP_OUTPUT_FILE" | grep -E '([0-9]+)/tcp'
  
  # Look for web servers
  web_ports=$(grep -E '([0-9]+)/tcp.*http' "$NMAP_OUTPUT_FILE" 2>/dev/null | grep -o -E '[0-9]+/tcp' | cut -d'/' -f1)
  
  # Check if nmap scan is complete
  if grep -q 'Nmap done' "$NMAP_OUTPUT_FILE" 2>/dev/null; then
    if [ -z "$web_ports" ]; then
      echo 'Scan complete. No web servers found.'
      break
    else
      echo "Scan complete. Found web servers on ports: $web_ports"
      break
    fi
  fi
  
  # If web ports were found but scan is not complete yet
  if [ ! -z "$web_ports" ]; then
    echo "Web servers found on ports: $web_ports. Will scan when nmap completes."
  else
    echo "No web servers found yet. Continuing to monitor..."
  fi
  
  sleep 10
done

# Run feroxbuster against each discovered web port
if [ ! -z "$web_ports" ]; then
  for port in $web_ports; do
    echo "Starting feroxbuster scan on port $port"
    feroxbuster -u "http://$TARGET_IP:$port" -x txt,html,php -o "feroxbuster_${TARGET_IP}_$port.txt"
  done
else
  echo "No web servers to scan."
fi