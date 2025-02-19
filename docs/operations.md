# MCP Translation Server Operations Guide

## Deployment

### Using Docker

1. Build and start the services:
```bash
docker-compose up -d
```

2. Check service status:
```bash
docker-compose ps
```

3. View logs:
```bash
docker-compose logs -f translation-server
```

### Manual Deployment

1. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
export FLASK_ENV=production
export MAX_WORKERS=4
export CACHE_SIZE=1000
```

3. Start the server:
```bash
python server.py
```

## Monitoring

### Metrics

Key metrics to monitor:
- Translation latency (95th percentile)
- Error rate
- Cache hit rate
- Memory usage
- CPU usage

### Prometheus

Access Prometheus UI:
```
http://localhost:9090
```

### Grafana

Access Grafana dashboards:
```
http://localhost:3000
```

Default credentials:
- Username: admin
- Password: admin

## Maintenance

### Backup

1. Backup resources:
```bash
./scripts/backup.sh
```

2. Backup configuration:
```bash
./scripts/backup-config.sh
```

### Updates

1. Update dependencies:
```bash
pip install -r requirements.txt --upgrade
```

2. Update Docker images:
```bash
docker-compose pull
docker-compose up -d
```

### Resource Management

1. Update language resources:
```bash
python scripts/update_resources.py
```

2. Validate resources:
```bash
python scripts/validate_resources.py
```

## Troubleshooting

### Common Issues

1. High Latency
- Check system resources
- Verify cache settings
- Review concurrent requests

2. Memory Issues
- Check memory usage
- Verify resource limits
- Consider scaling

3. Cache Problems
- Verify cache configuration
- Check cache hit rate
- Consider prewarming

### Debug Mode

Enable debug mode:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
```

### Logs

Access logs:
```bash
tail -f logs/translation-server.log
```

## Scaling

### Horizontal Scaling

1. Update docker-compose.yml:
```yaml
services:
  translation-server:
    deploy:
      replicas: 3
```

2. Apply changes:
```bash
docker-compose up -d --scale translation-server=3
```

### Vertical Scaling

Adjust resource limits in docker-compose.yml:
```yaml
services:
  translation-server:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Security

### SSL/TLS

1. Configure SSL certificates:
```bash
./scripts/setup-ssl.sh
```

2. Update nginx configuration:
```bash
./scripts/update-nginx-config.sh
```

### Access Control

1. Configure authentication:
```bash
python scripts/setup_auth.py
```

2. Manage API keys:
```bash
python scripts/manage_api_keys.py
```
