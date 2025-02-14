sudo apt update
sudo apt install certbot python3-certbot-dns-cloudflare
mkdir -p ./build/certbot
source .env
echo "dns_cloudflare_api_token = ${CLOUDFLARE_API_TOKEN_DNS01}" > ./build/certbot/cloudflare.ini
chmod 600 ./build/certbot/cloudflare.ini
certbot certonly --dns-cloudflare --dns-cloudflare-credentials ./build/certbot/cloudflare.ini -d line.provider.ayaka.lexa.digital --non-interactive --agree-tos --email ${CERTBOT_EMAIL} --config-dir ./build/letsencrypt/config --work-dir ./build/letsencrypt/work --logs-dir ./build/letsencrypt/logs
chmod +x Scripts/cron-certbot_renew.sh 
sudo ./Scripts/cron-certbot_renew.sh
mkdir -p ./build/cloudflared/
cd ./build/cloudflared/
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
./build/cloudflared/cloudflared tunnel login
mv ~/.cloudflared/cert.pem ./build/cloudflared/
rm -r ~/.cloudflared/
export TUNNEL_ID=$(./build/cloudflared/cloudflared tunnel --origincert=./build/cloudflared/cert.pem create Ayaka-Providers-LINE | grep -oP '(?<=Created tunnel Ayaka-Providers-LINE with id )[\w-]+')
grep -q "CLOUDFLARE_TUNNEL_ID=" .env && sed -i "s|^CLOUDFLARE_TUNNEL_ID=.*|CLOUDFLARE_TUNNEL_ID=$TUNNEL_ID|" .env || echo -e "\nCLOUDFLARE_TUNNEL_ID=$TUNNEL_ID" >> .env
set -a
source .env
set +a
if [ -z "$CLOUDFLARE_TUNNEL_ID" ] || [ -z "$CLOUDFLARE_API_TOKEN_DNS01" ]; then
	echo "Error: CLOUDFLARE_TUNNEL_ID and CLOUDFLARE_API_TOKEN_DNS01 must be set in .env"
	exit 1
fi
echo "Creating directories..."
mkdir -p ./build/certbot
mkdir -p ./build/.cloudflared
mkdir -p config/cloudflared
echo "Creating config in ./build/.cloudflared/config.yml..."
envsubst '${CLOUDFLARE_TUNNEL_ID}' < config/cloudflared/config.yml.template > ./build/cloudflared/config.yml
echo "Creating Certbot Cloudflare credentials in ./build/certbot/cloudflare.ini..."
echo "dns_cloudflare_api_token = ${CLOUDFLARE_API_TOKEN_DNS01}" > ./build/certbot/cloudflare.ini
chmod 600 ./build/certbot/cloudflare.ini
if ! grep -q "^tunnel: ${CLOUDFLARE_TUNNEL_ID}$" ./build/cloudflared/config.yml; then
	echo "Error: Config file was not created correctly"
	exit 1
fi
if [ ! -f ./build/cloudflared/cert.pem ]; then
	echo "Logging in to Cloudflare..."
	cloudflared tunnel login
fi
if ! ./build/cloudflared/cloudflared tunnel list | grep -q "${CLOUDFLARE_TUNNEL_ID}"; then
	echo "Error: Cloudflared tunnel ID does not exist in tunnels list. It must be re-created."
	exit 1
fi
echo "Setting up DNS..."
./build/cloudflared/cloudflared tunnel route dns "${CLOUDFLARE_TUNNEL_ID}" line.providers.ayaka.lexa.digital || {echo "DNS route already exists, skipping..."}
echo "Setup complete! Config is in ./build/cloudflared/config.yml and credentials in ./build/certbot/cloudflare.ini"
mkdir -p .cloudflared
cp ./build/.cloudflared/${CLOUDFLARE_TUNNEL_ID}.json .cloudflared/ || {
echo "Warning: Could not copy credentials file. This is normal for first-time setup."
}