# Ayaka LINE Integration

**This repository** implements a microservice bridging Ayaka's LLM application (via LangServe) to LINE, leveraging FastAPI, Uvicorn, and Cloudflared with Let's Encrypt SSL.

## Overview

1. **Single Script Deployment**  
   - `./Scripts/cloudflared-build.sh` will build all necessary Cloudflared files by merging environment variables from `.env` with templates in `./src/config`.  
   - `./Scripts/cloudflared-clean.sh` will remove all Cloudflared configs, purging any deployment-specific files if we need to reset.

2. **Execution Scripts**  
   - `./_START_APPLICATION.sh`: Starts the application server, including LangServe, FastAPI, and the Let's Encrypt agent (if applicable).  
   - `./_START_TUNNEL.sh`: Spins up the secure Cloudflared tunnel.

3. **Domain & SSL**  
   - A Let's Encrypt certificate will be configured for `line.provider.ayaka.lexa.digital`.  
   - The entire microservice will securely handle HTTP requests via HTTPS.

4. **Security Rules**  
   - Absolutely no files (especially credentials or config) will be created above the project root directory.  
   - **No sensitive information** is committed; all secrets stay in `.env` or generated into `./build/`.  
   - If you see a security concern, address it immediately.

5. **Installation & Usage**  
   - Place your sensitive credentials (Cloudflare tokens, LINE tokens, etc.) in `.env`.  
   - Run `./Scripts/cloudflared-build.sh` to generate necessary deployment files.  
   - Run `./_START_APPLICATION.sh` to start the LLM microservice and any background tasks.  
   - Run `./_START_TUNNEL.sh` to open a Cloudflared tunnel to `line.provider.ayaka.lexa.digital`.

## Setup & Installation

### 1. Environment Setup
Create a `.env` file with the following variables:
```ini
CLOUDFLARE_API_TOKEN_DNS01=your_cloudflare_api_token  # Token with DNS edit permissions
CERTBOT_EMAIL=your_email@example.com                  # Email for Let's Encrypt notifications
```

### 2. Initial Setup
Run the build script to set up SSL certificates, create the tunnel, and configure everything:
```bash
./Scripts/cloudflared-build.sh
```
This script will:
- Install required packages (certbot and plugins)
- Set up Let's Encrypt certificates using DNS validation
- Download and configure cloudflared
- Create a new tunnel and add its ID to your .env file
- Configure DNS routing
- Generate all necessary config files in ./build/

### 3. Starting the Service
```bash
# Start the tunnel using the generated configuration
./_START_TUNNEL.sh
```

### 4. Verification
- Check that the tunnel is running: `./build/cloudflared/cloudflared tunnel list`
- Verify DNS is configured: `./build/cloudflared/cloudflared tunnel route dns list`
- Test the endpoint: `curl -I https://line.provider.ayaka.lexa.digital/providers/line`

## Contributing

1. **Proposals & Ideas**: Update `PROJECT.md` with major changes or new approaches.  
2. **Security**: Always keep an eye out for ways to improve security.  
3. **Pull Requests**: Must pass linting and security checks before merging.
