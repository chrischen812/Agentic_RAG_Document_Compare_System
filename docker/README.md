# Docker Deployment for Agentic RAG System

This directory contains Docker configuration files for deploying the Agentic RAG System in containerized environments.

## Quick Start

### Development Environment

1. **Start development container:**
   ```bash
   cd docker
   docker-compose -f docker-compose.dev.yml up --build
   ```

2. **Access the application:**
   - API: http://localhost:5000
   - Documentation: http://localhost:5000/docs


## Configuration Files

### Dockerfile
Multi-stage Docker build optimized for production:
- **Builder stage**: Installs dependencies and build tools
- **Production stage**: Minimal runtime environment with security hardening
- Non-root user execution
- Health checks included

### docker-compose.dev.yml
Development environment with:
- Live code mounting for hot reload
- Development tools included
- Extended debugging capabilities


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
