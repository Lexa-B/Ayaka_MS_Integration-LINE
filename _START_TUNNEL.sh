clear
# Cleanup any existing tunnel
./build/cloudflared/cloudflared tunnel cleanup $CLOUDFLARE_TUNNEL_ID

# Start the tunnel (debug mode)
./build/cloudflared/cloudflared tunnel --loglevel trace --transport-loglevel trace --config ./build/cloudflared/config.yml run 2>&1 | tee ./logs/cloudflared.log

# Start the tunnel (silent mode)
#./build/cloudflared/cloudflared tunnel --config=./build/cloudflared/config.yml run