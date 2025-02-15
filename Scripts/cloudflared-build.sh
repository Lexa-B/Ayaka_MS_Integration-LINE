# Scripts/cloudflared-build.sh
clear
#!/usr/bin/env bash
set -e

chmod 744 ./config/cloudflared/config.yml.template

# Source environment variables
set -a
source .env
set +a

# Set up Cloudflared
echo "Setting up Cloudflared..."
mkdir -p ./build/cloudflared/
cd ./build/cloudflared/
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod 744 cloudflared

# Log in to Cloudflare and create tunnel
cd ../..
whoami
stat -c '%U' ./build/cloudflared/cloudflared
ls -l ./build/cloudflared/
./build/cloudflared/cloudflared tunnel login
mv ~/.cloudflared/cert.pem ./build/cloudflared/
rm -r ~/.cloudflared/
chmod 600 ./build/cloudflared/cert.pem

stat -c '%U' ./config/cloudflared/config.yml.template
# Create or use existing tunnel
export TUNNEL_ID=$(./build/cloudflared/cloudflared tunnel --origincert=./build/cloudflared/cert.pem create Ayaka-Providers-LINE | grep -oP '(?<=Created tunnel Ayaka-Providers-LINE with id )[\w-]+')
grep -q "CLOUDFLARE_TUNNEL_ID=" .env && sed -i "s|^CLOUDFLARE_TUNNEL_ID=.*|CLOUDFLARE_TUNNEL_ID=$TUNNEL_ID|" .env || echo -e "\nCLOUDFLARE_TUNNEL_ID=$TUNNEL_ID" >> .env

# Refresh environment variables
set -a
source .env
set +a

# Verify environment variables are set
if [ -z "$CLOUDFLARE_TUNNEL_ID" ] || [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "Error: CLOUDFLARE_TUNNEL_ID and CLOUDFLARE_API_TOKEN must be set in .env"
    exit 1
fi

# Generate Cloudflared config
echo "Generating Cloudflared configuration..."
envsubst '${CLOUDFLARE_TUNNEL_ID}' < ./config/cloudflared/config.yml.template > ./build/cloudflared/config.yml

# Verify config
if ! grep -q "^tunnel: ${CLOUDFLARE_TUNNEL_ID}$" ./build/cloudflared/config.yml; then
    echo "Error: Config file was not created correctly"
    exit 1
fi

# Verify tunnel ID exists
if ! ./build/cloudflared/cloudflared tunnel list | grep -q "${CLOUDFLARE_TUNNEL_ID}"; then
    echo "Error: Cloudflared tunnel ID does not exist in tunnels list. It must be re-created."
    exit 1
fi

# Set up DNS route
echo "Setting up DNS routing..."
./build/cloudflared/cloudflared tunnel route dns "${CLOUDFLARE_TUNNEL_ID}" line.provider.ayaka.lexa.digital || {echo "DNS route already exists, skipping..."}

# Update the config to point directly to the archive files
echo "Updating Cloudflared configuration to point to archive files..."
sed -i "s|^tunnel: ${CLOUDFLARE_TUNNEL_ID}$|tunnel: ${CLOUDFLARE_TUNNEL_ID}|" ./build/cloudflared/config.yml

if [ ! -f ./build/cloudflared/cert.pem ]; then
	echo "Logging in to Cloudflare..."
	cloudflared tunnel login
fi
if ! ./build/cloudflared/cloudflared tunnel list | grep -q "${CLOUDFLARE_TUNNEL_ID}"; then
	echo "Error: Cloudflared tunnel ID does not exist in tunnels list. It must be re-created."
	exit 1
fi

echo "Setup complete! Config is in ./build/cloudflared/config.yml and credentials in ./build/certbot/cloudflare.ini"
