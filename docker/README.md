# Docker Deployment for Agentic RAG System

This directory contains Docker configuration files for deploying the Agentic RAG System in containerized environments.

## Quick Start

### Development Environment

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

2. **Start development container:**
   ```bash
   cd docker
   docker-compose -f docker-compose.dev.yml up --build
   ```

3. **Access the application:**
   - API: http://localhost:5000
   - Documentation: http://localhost:5000/docs

### Production Environment

1. **Build and start production containers:**
   ```bash
   cd docker
   docker-compose up --build -d
   ```

2. **With Nginx reverse proxy:**
   ```bash
   docker-compose --profile production up --build -d
   ```

## Configuration Files

### Dockerfile
Multi-stage Docker build optimized for production:
- **Builder stage**: Installs dependencies and build tools
- **Production stage**: Minimal runtime environment with security hardening
- Non-root user execution
- Health checks included

### docker-compose.yml
Production deployment with:
- Persistent data volumes
- Environment variable configuration
- Health checks and restart policies
- Optional Nginx reverse proxy

### docker-compose.dev.yml
Development environment with:
- Live code mounting for hot reload
- Development tools included
- Extended debugging capabilities

### nginx.conf
Production-ready Nginx configuration with:
- Rate limiting for API endpoints
- Security headers
- File upload optimization
- SSL/HTTPS support (commented)

## Environment Variables

Create a `.env` file in the docker directory:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
ENVIRONMENT=production
HOST=0.0.0.0
PORT=5000
```

## Volumes and Data Persistence

- **rag_data**: Persistent storage for ChromaDB and document embeddings
- **documents**: Optional mount point for easy document access
- **ssl**: SSL certificates for HTTPS (production)

## Health Checks

The container includes health checks that verify:
- Application is responding on port 5000
- API endpoints are accessible
- Dependencies are properly initialized

## Production Deployment

### Basic Deployment
```bash
# Clone repository
git clone <your-repo>
cd <repo-name>

# Set up environment
cd docker
cp .env.example .env
# Edit .env with your API keys

# Deploy
docker-compose up --build -d

# View logs
docker-compose logs -f rag-api
```

### With Reverse Proxy
```bash
# Deploy with Nginx
docker-compose --profile production up --build -d

# Access via HTTP/HTTPS
curl http://localhost/api/documents
```

### Scaling (Future Enhancement)
```bash
# Scale API containers
docker-compose up --scale rag-api=3 -d
```

## Security Considerations

1. **Non-root execution**: Application runs as `appuser`
2. **Minimal attack surface**: Production image uses `python:3.11-slim`
3. **Security headers**: Nginx adds security headers
4. **Rate limiting**: API endpoints are rate-limited
5. **Input validation**: File upload size limits enforced

## Monitoring and Logging

```bash
# View application logs
docker-compose logs -f rag-api

# Check container health
docker-compose ps

# Monitor resource usage
docker stats

# Execute commands in container
docker-compose exec rag-api bash
```

## Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8000:5000"  # Use port 8000 instead
   ```

2. **Memory issues:**
   ```bash
   # Add memory limits
   deploy:
     resources:
       limits:
         memory: 2G
   ```

3. **Permission issues:**
   ```bash
   # Fix volume permissions
   docker-compose exec rag-api chown -R appuser:appuser /app/data
   ```

## Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Backup Data
```bash
# Backup ChromaDB
docker-compose exec rag-api tar -czf /tmp/backup.tar.gz /app/data
docker cp agentic-rag-api:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz
```

### Clean Up
```bash
# Remove containers and networks
docker-compose down

# Remove images
docker-compose down --rmi all

# Remove volumes (WARNING: deletes all data)
docker-compose down --volumes
```