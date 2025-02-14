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

## Additional Considerations

### 1. Let's Encrypt & Cloudflare
This system must run behind Cloudflare DNS, using a nested subdomain (e.g., `line.provider.ayaka.lexa.digital`) and a secure Cloudflared tunnel. The primary goal is to encrypt all traffic to/from LINE.

**Option A:** Use Cloudflare's proxy (Full SSL mode) and rely on your Let's Encrypt certificate.  
**Option B:** Use Cloudflare's DNS challenge for Let's Encrypt (DNS-01) if direct port 80/443 is not available.  
**Analysis:** Since the connection from LINE is through Cloudflared, we must ensure the certificate is valid and recognized by LINE. If direct inbound connections on 80/443 aren't possible, using DNS-01 or a Cloudflare-based SSL approach can handle the ACME challenges. The main requirement is end-to-end encryption, which is achieved if Cloudflare terminates SSL and the tunnel is also encrypted.

### 2. LangServe & Concurrency
For this pre-alpha proof-of-concept, we'll do basic concurrency limiting. LangServe can be set to a modest worker limit or a simple rate limit. Since resource usage is not the primary worry now, we won't implement autoscaling. But for production, we might implement more robust concurrency controls.

### 3. Environment Variables
All secrets (Cloudflare tokens, LINE tokens, etc.) remain in `.env`. We'll define a rotation schedule or at least a procedure to manually rotate expired tokens. Monitoring logs should warn us if an API key is invalid (because requests would fail). We will rely on error logging to detect key expiry.

### 4. Logging & Monitoring
We'll use [DramaticLogger](https://github.com/Lexa-B/DramaticLogger.git) for local logging in this initial implementation. Each script/action logs errors and important events. Over time, we can extend to a centralized logging system, but for now we only require local logs for debugging.

### 5. Local & Remote Paths (Validations?)
By "validations," we mean how Let's Encrypt obtains and verifies domain ownership. Typically, HTTP-01 or TLS-ALPN-01 challenges require direct inbound connections on port 80/443. If the environment prevents that, using DNS-01 (where we create a TXT record in Cloudflare DNS) might be required. Because we're behind nested subdomains and Cloudflared, DNS validations often work best.

### 6. Docker vs. Non-Docker
The final production environment will use Docker (with a `Dockerfile` and `docker-compose.yml`). However, everything should also run in the WSL dev environment natively without any changes. This ensures consistency and easy iteration while developing. Eventually, the same code and config can be containerized for production.

## Implementation Plan

### Phase 1: High-Risk Components

1. **SSL/Domain Setup** (Most Complex)
   - **Determine Challenge Type**:
     - Research and decide between DNS-01 and HTTP-01 based on infrastructure.
   - **Set Up Cloudflare DNS for Subdomain**:
     - Create necessary DNS records in Cloudflare.
   - **Implement Let's Encrypt Certificate Automation**:
     - Script the certificate issuance and renewal process.
   - **Test SSL Chain Validation**:
     - Verify certificate validity and trust chain through testing tools.
   - **Document in README**:
     - Provide step-by-step instructions and troubleshooting tips.

2. **Cloudflared Tunnel Architecture**
   - Design template system for tunnel configs
   - Create build/clean scripts with proper error handling
   - Implement credential rotation handling
   - Test tunnel stability and reconnection
   - Document tunnel setup and troubleshooting in README

3. **Environment Management**
   - Create comprehensive .env template
   - Document all required variables
   - Implement validation checks
   - Add expiry monitoring for tokens
   - Document environment setup in README

### Phase 2: Critical Components

4. **LINE Integration**
   - Implement webhook endpoint
   - Set up message handling
   - Add signature verification
   - Test LINE API interaction
   - Document LINE integration setup in README

5. **Logging System**
   - Integrate DramaticLogger
   - Define log levels and formats
   - Implement rotation and cleanup
   - Add error monitoring
   - Document logging configuration in README

### Phase 3: Core Features

6. **LangServe Integration**
   - Set up basic LangServe endpoint
   - Implement concurrency controls
   - Test LLM response handling
   - Verify memory usage and performance
   - Document LangServe setup in README

7. **Docker Configuration**
   - Create Dockerfile
   - Set up docker-compose
   - Test both WSL and Docker environments
   - Verify identical behavior
   - Document Docker setup in README

### Phase 4: Support Systems

8. **Monitoring System**
   - Set up basic monitoring
   - Implement error tracking
   - Test alerting
   - Automated reissuance of certificates
   - Token rotation scheme
   - Document monitoring setup in README

### Dependencies
- SSL and Cloudflared must be working before LINE integration
- Environment template needed before any other component
- Logging should be implemented early for debugging
- Docker and LangServe can be added once core features work

### Success Criteria
- All components work identically in WSL and Docker
- SSL is properly terminated and validated
- LINE messages flow bidirectionally
- Logs capture all significant events
- No sensitive data exposed in repo
- Documentation is complete and accurate

### Risk Assessment

#### Phase 1: SSL/Domain Setup
- **Risk**: Failure in certificate automation could lead to service downtime.
- **Mitigation**: Implement retry mechanisms and maintain backup certificates.

#### Phase 2: LINE Integration
- **Risk**: Misconfigured webhooks may lead to unresponsive bots.
- **Mitigation**: Thoroughly test webhook endpoints with various LINE events.

### Version Control Strategy

- **Branching Model**: Use Git Flow with `main`, [author]-Dev, and feature branches.
- **Commit Messages**: Follow the Conventional Commits standard for clarity.
- **Pull Requests**: Require code reviews and pass CI checks before merging.

### Backup and Recovery

- **Configuration Backups**: Regularly back up `./build/` and `.env` files.
- **Disaster Recovery Plan**: Outline steps to restore services in case of major failures.
