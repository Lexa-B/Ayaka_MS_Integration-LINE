#!/bin/bash

#!/bin/bash

# Check if the script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Please use sudo or log in as root."
    exit 1
fi

# Define the cron job to be added
cron_job='0 3 * * * certbot renew --quiet --deploy-hook "cloudflared tunnel reload"'

# Check if the cron job already exists
crontab -l -u root 2>/dev/null | grep -F "$cron_job" >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Cron job already exists. No changes made."
else
    # Add the new cron job
    (crontab -l -u root 2>/dev/null; echo "$cron_job") | crontab -u root -
    echo "Cron job added successfully."
fi

