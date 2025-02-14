# Integration Between Ayaka (LLM) and LINE

This microservice is the integration between Ayaka's LLM application and LINE. The main technologies and goals are:

1. **Technologies**  
   - **LangServe**: Exposes the LLM as an API  
   - **FastAPI** & **Uvicorn**: Handles incoming requests and routes  
   - **Cloudflared**: Provides secure tunneling and reverse proxy  
   - **Let's Encrypt SSL**: Ensures HTTPS to the domain (line.provider.ayaka.lexa.digital)  

2. **Deployment Approach**  
   - A single script `./Scripts/cloudflared-build.sh` will create all deployment-specific Cloudflared files by combining templates located in `./src/config` with sensitive fields from `.env`.  
   - A cleanup script `./Scripts/cloudflared-clean.sh` will remove all Cloudflared configs and related files, ensuring we can purge them completely if needed.  
   - Additional scripts:
     - `./_START_APPLICATION.sh` launches the LangServe interface, FastAPI, and any background services needed (like the Let's Encrypt agent).  
     - `./_START_TUNNEL.sh` starts the Cloudflared tunnel.  

3. **Domain and SSL**  
   - The microservice will be accessible via `line.provider.ayaka.lexa.digital` and will use Let's Encrypt SSL certificates.  
   - **No** sensitive information (tokens, secrets, etc.) will be committed to source control.  

4. **Security Considerations**  
   - **No files** will be created outside the project root.  
   - **No sensitive information** will be saved anywhere except in `.env` and in `./build/` (or ephemeral usage during script execution).  
   - Security is critical at every step. If a vulnerability or risk is noticed, it must be addressed immediately.

## Next Steps

- We will flesh out the scripts one by one, ensuring minimal risk of secrets being exposed.  
- Once the basic skeleton is in place, we will document the precise routines inside `README.md`.
