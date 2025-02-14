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

## Contributing

1. **Proposals & Ideas**: Update `PROJECT.md` with major changes or new approaches.  
2. **Security**: Always keep an eye out for ways to improve security.  
3. **Pull Requests**: Must pass linting and security checks before merging.
