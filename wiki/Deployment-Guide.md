# Deployment Guide

Complete guide for deploying tail-lookup in various environments, from simple Docker containers to production Kubernetes clusters.

## Quick Start

### Docker (Simplest)

Pull and run the latest image:

```bash
docker run -d \
  --name tail-lookup \
  -p 8080:8080 \
  --restart unless-stopped \
  ryakel/tail-lookup:latest
```

Access at: http://localhost:8080

### Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  tail-lookup:
    image: ryakel/tail-lookup:latest
    container_name: tail-lookup
    ports:
      - "8080:8080"
    restart: unless-stopped
```

Deploy:

```bash
docker compose up -d
```

---

## Deployment Options

### 1. Local Docker Deployment

**Use case**: Local development, testing, personal use

**Steps**:

1. **Pull latest image**:
   ```bash
   docker pull ryakel/tail-lookup:latest
   ```

2. **Run container**:
   ```bash
   docker run -d \
     --name tail-lookup \
     -p 8080:8080 \
     --restart unless-stopped \
     ryakel/tail-lookup:latest
   ```

3. **Verify**:
   ```bash
   curl http://localhost:8080/api/v1/health
   ```

4. **View logs**:
   ```bash
   docker logs -f tail-lookup
   ```

5. **Stop/Start**:
   ```bash
   docker stop tail-lookup
   docker start tail-lookup
   ```

6. **Update**:
   ```bash
   docker pull ryakel/tail-lookup:latest
   docker stop tail-lookup
   docker rm tail-lookup
   docker run -d --name tail-lookup -p 8080:8080 --restart unless-stopped ryakel/tail-lookup:latest
   ```

**Pros**:
- Simple, single command
- No configuration needed
- Fast startup

**Cons**:
- Manual updates
- No automatic restart on reboot (unless using --restart)

---

### 2. Docker Compose Deployment

**Use case**: Production single-host deployments, easier management

**Steps**:

1. **Create docker-compose.yml**:
   ```yaml
   version: "3.8"

   services:
     tail-lookup:
       image: ryakel/tail-lookup:latest
       container_name: tail-lookup
       ports:
         - "8080:8080"
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8080/api/v1/health').raise_for_status()"]
         interval: 30s
         timeout: 5s
         retries: 3
         start_period: 5s
   ```

2. **Deploy**:
   ```bash
   docker compose up -d
   ```

3. **View logs**:
   ```bash
   docker compose logs -f
   ```

4. **Update**:
   ```bash
   docker compose pull
   docker compose up -d
   ```

5. **Stop**:
   ```bash
   docker compose down
   ```

**Pros**:
- Declarative configuration
- Easy updates with docker compose pull
- Health check built-in
- Simple scaling (if needed)

**Cons**:
- Requires docker-compose.yml file
- Still manual updates

---

### 3. Portainer Deployment

**Use case**: Production with web UI, automatic updates

**Prerequisites**:
- Portainer installed: https://docs.portainer.io/start/install

**Steps**:

1. **In Portainer UI**:
   - Navigate to "Stacks" → "Add stack"
   - Name: `tail-lookup`
   - Web editor, paste:

   ```yaml
   version: "3.8"

   services:
     tail-lookup:
       image: ryakel/tail-lookup:latest
       ports:
         - "8080:8080"
       restart: unless-stopped
   ```

   - Click "Deploy the stack"

2. **Enable webhook for automatic updates**:
   - Navigate to stack → "Webhook"
   - Toggle "Service webhook"
   - Copy webhook URL
   - Add to GitHub repository secrets as `PORTAINER_WEBHOOK_URL`

3. **Manual update**:
   - Stack → "Update" → "Pull and redeploy"

**Pros**:
- Web UI for management
- Automatic updates via webhook
- Easy rollback
- Multi-host support (Portainer Business)

**Cons**:
- Requires Portainer installation
- Additional complexity

---

### 4. Watchtower Auto-Update

**Use case**: Automatic updates without webhooks

**Steps**:

1. **Create docker-compose.yml with Watchtower**:
   ```yaml
   version: "3.8"

   services:
     tail-lookup:
       image: ryakel/tail-lookup:latest
       container_name: tail-lookup
       ports:
         - "8080:8080"
       restart: unless-stopped

     watchtower:
       image: containrrr/watchtower
       container_name: watchtower
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock
       command: --interval 3600 tail-lookup
       restart: unless-stopped
   ```

2. **Deploy**:
   ```bash
   docker compose up -d
   ```

**How it works**:
- Watchtower checks for image updates every hour
- Automatically pulls new image if available
- Gracefully restarts tail-lookup container
- Zero manual intervention

**Pros**:
- Fully automatic updates
- No webhook configuration needed
- Works with any Docker deployment

**Cons**:
- Additional container running
- Polls Docker Hub (might hit rate limits)
- Updates happen automatically (no approval)

---

### 5. Kubernetes Deployment

**Use case**: Large-scale, multi-instance deployments

**Prerequisites**:
- Kubernetes cluster (minikube, EKS, GKE, AKS, etc.)
- kubectl configured

**Deployment Manifest** (`tail-lookup-deployment.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tail-lookup
  labels:
    app: tail-lookup
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tail-lookup
  template:
    metadata:
      labels:
        app: tail-lookup
    spec:
      containers:
      - name: tail-lookup
        image: ryakel/tail-lookup:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: tail-lookup
spec:
  type: LoadBalancer
  selector:
    app: tail-lookup
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
```

**Deploy**:

```bash
kubectl apply -f tail-lookup-deployment.yaml
```

**Get service URL**:

```bash
kubectl get svc tail-lookup
```

**Update**:

```bash
kubectl rollout restart deployment/tail-lookup
```

**Scale**:

```bash
kubectl scale deployment/tail-lookup --replicas=5
```

**Pros**:
- High availability (multiple replicas)
- Automatic load balancing
- Rolling updates
- Self-healing
- Horizontal scaling

**Cons**:
- Complex setup
- Requires Kubernetes knowledge
- Overkill for small deployments

---

### 6. Cloud Platform Deployments

#### AWS ECS (Elastic Container Service)

**Task Definition**:

```json
{
  "family": "tail-lookup",
  "containerDefinitions": [
    {
      "name": "tail-lookup",
      "image": "ryakel/tail-lookup:latest",
      "memory": 256,
      "cpu": 256,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/api/v1/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 10
      }
    }
  ]
}
```

Deploy via:
- AWS Console → ECS → Create Service
- AWS CLI: `aws ecs create-service ...`
- Terraform/CloudFormation for IaC

#### Google Cloud Run

```bash
gcloud run deploy tail-lookup \
  --image ryakel/tail-lookup:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

**Pros**: Fully managed, auto-scaling, pay-per-use

#### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name tail-lookup \
  --image ryakel/tail-lookup:latest \
  --ports 8080 \
  --dns-name-label tail-lookup-aci \
  --restart-policy Always
```

---

## Reverse Proxy Configuration

### Nginx

**Use case**: TLS termination, custom domain, multiple services

**nginx.conf**:

```nginx
server {
    listen 80;
    server_name tail-lookup.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tail-lookup.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Optional: serve static files directly
    location /static/ {
        proxy_pass http://localhost:8080/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Traefik

**docker-compose.yml with Traefik**:

```yaml
version: "3.8"

services:
  tail-lookup:
    image: ryakel/tail-lookup:latest
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.tail-lookup.rule=Host(`tail-lookup.example.com`)"
      - "traefik.http.routers.tail-lookup.entrypoints=websecure"
      - "traefik.http.routers.tail-lookup.tls.certresolver=letsencrypt"
      - "traefik.http.services.tail-lookup.loadbalancer.server.port=8080"
    networks:
      - traefik

networks:
  traefik:
    external: true
```

### Caddy

**Caddyfile**:

```caddy
tail-lookup.example.com {
    reverse_proxy localhost:8080
}
```

---

## Environment Configuration

### Port Mapping

Default internal port: **8080**

Map to different external port:

```bash
docker run -p 3000:8080 ryakel/tail-lookup:latest  # Access on port 3000
```

### Database Path (Custom Build)

If building custom image with different database:

```dockerfile
FROM ryakel/tail-lookup:latest
COPY my-custom.db /app/data/aircraft.db
```

No environment variable needed; path is hardcoded in Dockerfile.

---

## Health Checks

### Docker Health Check

Built into Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/api/v1/health').raise_for_status()"
```

Check container health:

```bash
docker inspect --format='{{.State.Health.Status}}' tail-lookup
```

### Kubernetes Probes

Liveness probe:
```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 30
```

Readiness probe:
```yaml
readinessProbe:
  httpGet:
    path: /api/v1/health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```

### External Monitoring

**UptimeRobot**:
- Monitor: `https://tail-lookup.example.com/api/v1/health`
- Interval: 5 minutes
- Alert on: Status != 200

**Prometheus**:
```yaml
scrape_configs:
  - job_name: 'tail-lookup'
    metrics_path: '/api/v1/health'
    static_configs:
      - targets: ['localhost:8080']
```

---

## Backup and Recovery

### Backup Strategy

**Database snapshots**:
- Automatically stored in GitHub Releases (daily)
- Download: `curl -L -o aircraft.db https://github.com/ryakel/tail-lookup/releases/latest/download/aircraft.db`

**Container backup** (not typically needed):
- Database is immutable in container
- Just pull latest image to restore

### Disaster Recovery

**Scenario**: Container lost, need to restore

1. Pull latest image:
   ```bash
   docker pull ryakel/tail-lookup:latest
   ```

2. Redeploy:
   ```bash
   docker run -d -p 8080:8080 --restart unless-stopped ryakel/tail-lookup:latest
   ```

**Scenario**: Need specific historical database

1. Download from release:
   ```bash
   curl -L -o aircraft.db https://github.com/ryakel/tail-lookup/releases/download/data-2025-11-20/aircraft.db
   ```

2. Build custom image:
   ```dockerfile
   FROM ryakel/tail-lookup:latest
   COPY aircraft.db /app/data/aircraft.db
   ```

3. Build and run:
   ```bash
   docker build -t tail-lookup:custom .
   docker run -d -p 8080:8080 tail-lookup:custom
   ```

---

## Scaling Considerations

### Vertical Scaling (Bigger Container)

Adjust resource limits:

**Docker**:
```bash
docker run -d \
  --name tail-lookup \
  -p 8080:8080 \
  --memory=512m \
  --cpus=1.0 \
  ryakel/tail-lookup:latest
```

**Kubernetes**:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "1000m"
```

### Horizontal Scaling (More Containers)

**Load Balancer Required**:
- Nginx, HAProxy, Traefik, or cloud load balancer
- Round-robin or least-connections algorithm

**Docker Compose (simple)**:
```yaml
version: "3.8"

services:
  tail-lookup:
    image: ryakel/tail-lookup:latest
    deploy:
      replicas: 3
    ports:
      - "8080-8082:8080"
```

**Kubernetes (production)**:
```yaml
spec:
  replicas: 5  # Run 5 instances
```

**Database considerations**:
- Each container has full database copy
- Read-only workload, no synchronization needed
- No shared state between containers
- Perfect for horizontal scaling

### Performance Tuning

**Database optimization** (already done):
- SQLite with JOIN index
- Batch inserts during build
- Read-only mode (no write locks)

**Application optimization** (already done):
- Async FastAPI with Uvicorn
- Pydantic validation
- No external API calls

**Container optimization**:
- Use date-tagged images (not latest) for consistency
- Enable Docker BuildKit for faster builds
- Use multi-stage builds (not applicable here)

---

## Security Best Practices

### Network Security

**Firewall rules**:
- Allow inbound on port 8080 (or your mapped port)
- Deny all other inbound traffic
- Allow outbound (for Docker Hub pulls)

**TLS/SSL**:
- Use reverse proxy (Nginx, Traefik, Caddy) for TLS termination
- Let's Encrypt for free certificates
- Redirect HTTP to HTTPS

**CORS**:
- Currently allows all origins (` Allow-Origin: *`)
- For production, consider restricting to specific domains

### Container Security

**Run as non-root** (future improvement):
```dockerfile
USER nobody
```

**Read-only root filesystem** (future improvement):
```bash
docker run --read-only --tmpfs /tmp ryakel/tail-lookup:latest
```

**Security scanning**:
```bash
docker scan ryakel/tail-lookup:latest
```

### Access Control

**No built-in authentication** (by design):
- Public FAA data, open access
- Add authentication with reverse proxy if needed

**Example with Nginx Basic Auth**:
```nginx
location / {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8080;
}
```

---

## Troubleshooting

### Container Won't Start

**Check logs**:
```bash
docker logs tail-lookup
```

**Common causes**:
- Port 8080 already in use: Change mapping `-p 8081:8080`
- Database file missing: Use official image, not custom build
- Python errors: Check Python version in Dockerfile

### Health Check Failing

**Manual check**:
```bash
curl http://localhost:8080/api/v1/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "database_exists": true,
  "record_count": 297431,
  "last_updated": "2025-11-28T06:15:23Z"
}
```

**If failing**:
- Verify container is running: `docker ps`
- Check database exists: `docker exec tail-lookup ls -lh /app/data/aircraft.db`
- Restart container: `docker restart tail-lookup`

### Stale Database

**Symptom**: `last_updated` is old (more than 24 hours)

**Solutions**:
1. Pull latest image: `docker pull ryakel/tail-lookup:latest`
2. Recreate container
3. Check nightly build workflow for failures

### High Memory Usage

**Normal**: ~100-150MB RAM usage

**High (>500MB)**: Possible memory leak

**Solutions**:
1. Restart container: `docker restart tail-lookup`
2. Check for long-running requests
3. Monitor with `docker stats tail-lookup`

---

## Monitoring and Logging

### Container Logs

**View logs**:
```bash
docker logs -f tail-lookup
```

**Log to file**:
```bash
docker logs tail-lookup > tail-lookup.log 2>&1
```

**Docker Compose logging**:
```yaml
services:
  tail-lookup:
    image: ryakel/tail-lookup:latest
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Application Metrics (Future)

**Prometheus metrics** (not yet implemented):
```python
# Add to main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

Access at: `http://localhost:8080/metrics`

### Uptime Monitoring

**Self-hosted** (Uptime Kuma):
```bash
docker run -d \
  --name uptime-kuma \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:latest
```

Add monitor for `http://tail-lookup:8080/api/v1/health`

---

## Cost Considerations

### Hosting Costs

**Self-hosted (VPS)**:
- Small VPS (1 vCPU, 1GB RAM): $5-10/month
- Can run many containers
- Example: DigitalOcean, Linode, Vultr

**Cloud Platforms**:
- AWS ECS: ~$15-30/month (Fargate)
- Google Cloud Run: ~$5-15/month (pay-per-use)
- Azure Container Instances: ~$10-20/month

**Kubernetes Cluster**:
- Managed: $50-150/month (EKS, GKE, AKS)
- Self-hosted: VPS costs only

### Bandwidth Costs

**Docker Hub pulls**:
- Free tier: 100 pulls per 6 hours (unauthenticated)
- Paid tier: Unlimited pulls
- Our usage: ~30 pulls/day (nightly builds + updates)

**API traffic**:
- Minimal bandwidth (JSON responses ~1-5KB)
- 100K requests/month ≈ 100-500MB
- Usually included in hosting

---

## Recommended Production Setup

For production deployment, we recommend:

1. **Infrastructure**:
   - Docker Compose on VPS (simple) or Kubernetes (complex)
   - Nginx reverse proxy for TLS
   - Automated updates (Watchtower or Portainer webhook)

2. **Monitoring**:
   - Health check endpoint monitoring (UptimeRobot, Uptime Kuma)
   - Container logs to external service (optional)
   - Alerting on failures (email, Slack)

3. **Security**:
   - TLS certificate (Let's Encrypt)
   - Firewall rules (only ports 80/443 open)
   - Regular image updates (automated)

4. **Backup**:
   - No backup needed (database in GitHub Releases)
   - Just redeploy latest image if container lost

**Example Production Stack**:
```yaml
version: "3.8"

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - tail-lookup

  tail-lookup:
    image: ryakel/tail-lookup:latest
    restart: unless-stopped
    expose:
      - "8080"

  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 3600 tail-lookup
```

---

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Let's Encrypt](https://letsencrypt.org/)
