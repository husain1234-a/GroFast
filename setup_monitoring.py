#!/usr/bin/env python3
"""
Monitoring and Observability Setup Script
Sets up comprehensive monitoring for the Blinkit clone application.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

def create_prometheus_config():
    """Create Prometheus configuration for metrics collection"""
    
    prometheus_config = {
        "global": {
            "scrape_interval": "15s",
            "evaluation_interval": "15s"
        },
        "rule_files": [],
        "scrape_configs": [
            {
                "job_name": "blinkit-main-app",
                "static_configs": [
                    {"targets": ["localhost:8000"]}
                ],
                "metrics_path": "/metrics",
                "scrape_interval": "15s"
            },
            {
                "job_name": "blinkit-api-gateway",
                "static_configs": [
                    {"targets": ["localhost:8080"]}
                ],
                "metrics_path": "/metrics",
                "scrape_interval": "15s"
            },
            {
                "job_name": "blinkit-microservices",
                "static_configs": [
                    {
                        "targets": [
                            "localhost:8001",  # auth-service
                            "localhost:8002",  # product-service
                            "localhost:8003",  # cart-service
                            "localhost:8004",  # order-service
                            "localhost:8005",  # delivery-service
                            "localhost:8006"   # notification-service
                        ]
                    }
                ],
                "metrics_path": "/metrics",
                "scrape_interval": "15s"
            }
        ]
    }
    
    # Create monitoring directory
    monitoring_dir = Path("monitoring")
    monitoring_dir.mkdir(exist_ok=True)
    
    # Write Prometheus config
    with open(monitoring_dir / "prometheus.yml", "w") as f:
        import yaml
        yaml.dump(prometheus_config, f, default_flow_style=False)
    
    print("✅ Created Prometheus configuration")

def create_grafana_dashboard():
    """Create Grafana dashboard configuration"""
    
    dashboard = {
        "dashboard": {
            "id": None,
            "title": "Blinkit Clone - Application Monitoring",
            "tags": ["blinkit", "microservices"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Request Rate",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(http_requests_total[5m])",
                            "legendFormat": "{{service}} - {{method}} {{status}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Response Time",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "95th percentile"
                        },
                        {
                            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "50th percentile"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                },
                {
                    "id": 3,
                    "title": "Error Rate",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(http_requests_total{status=~\"4..|5..\"}[5m])",
                            "legendFormat": "{{service}} - {{status}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                },
                {
                    "id": 4,
                    "title": "Active Requests",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "http_requests_active",
                            "legendFormat": "{{service}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                },
                {
                    "id": 5,
                    "title": "Health Check Status",
                    "type": "table",
                    "targets": [
                        {
                            "expr": "up",
                            "legendFormat": "{{job}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16}
                }
            ],
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "refresh": "5s"
        }
    }
    
    monitoring_dir = Path("monitoring")
    monitoring_dir.mkdir(exist_ok=True)
    
    with open(monitoring_dir / "grafana-dashboard.json", "w") as f:
        json.dump(dashboard, f, indent=2)
    
    print("✅ Created Grafana dashboard configuration")

def create_docker_compose_monitoring():
    """Create Docker Compose configuration for monitoring stack"""
    
    monitoring_compose = {
        "version": "3.8",
        "services": {
            "prometheus": {
                "image": "prom/prometheus:latest",
                "container_name": "blinkit-prometheus",
                "ports": ["9090:9090"],
                "volumes": [
                    "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"
                ],
                "command": [
                    "--config.file=/etc/prometheus/prometheus.yml",
                    "--storage.tsdb.path=/prometheus",
                    "--web.console.libraries=/etc/prometheus/console_libraries",
                    "--web.console.templates=/etc/prometheus/consoles",
                    "--storage.tsdb.retention.time=200h",
                    "--web.enable-lifecycle"
                ],
                "restart": "unless-stopped"
            },
            "grafana": {
                "image": "grafana/grafana:latest",
                "container_name": "blinkit-grafana",
                "ports": ["3000:3000"],
                "environment": [
                    "GF_SECURITY_ADMIN_PASSWORD=admin123"
                ],
                "volumes": [
                    "grafana-storage:/var/lib/grafana",
                    "./monitoring/grafana-dashboard.json:/var/lib/grafana/dashboards/blinkit.json"
                ],
                "restart": "unless-stopped"
            },
            "loki": {
                "image": "grafana/loki:latest",
                "container_name": "blinkit-loki",
                "ports": ["3100:3100"],
                "command": "-config.file=/etc/loki/local-config.yaml",
                "restart": "unless-stopped"
            },
            "promtail": {
                "image": "grafana/promtail:latest",
                "container_name": "blinkit-promtail",
                "volumes": [
                    "./logs:/var/log/blinkit",
                    "./monitoring/promtail-config.yml:/etc/promtail/config.yml"
                ],
                "command": "-config.file=/etc/promtail/config.yml",
                "restart": "unless-stopped"
            }
        },
        "volumes": {
            "grafana-storage": {}
        }
    }
    
    monitoring_dir = Path("monitoring")
    monitoring_dir.mkdir(exist_ok=True)
    
    with open(monitoring_dir / "docker-compose.monitoring.yml", "w") as f:
        import yaml
        yaml.dump(monitoring_compose, f, default_flow_style=False)
    
    print("✅ Created Docker Compose monitoring configuration")

def create_promtail_config():
    """Create Promtail configuration for log aggregation"""
    
    promtail_config = {
        "server": {
            "http_listen_port": 9080,
            "grpc_listen_port": 0
        },
        "positions": {
            "filename": "/tmp/positions.yaml"
        },
        "clients": [
            {"url": "http://loki:3100/loki/api/v1/push"}
        ],
        "scrape_configs": [
            {
                "job_name": "blinkit-logs",
                "static_configs": [
                    {
                        "targets": ["localhost"],
                        "labels": {
                            "job": "blinkit-logs",
                            "__path__": "/var/log/blinkit/*.log"
                        }
                    }
                ],
                "pipeline_stages": [
                    {
                        "json": {
                            "expressions": {
                                "timestamp": "timestamp",
                                "level": "level",
                                "service": "service_name",
                                "message": "message",
                                "request_id": "request_id"
                            }
                        }
                    },
                    {
                        "labels": {
                            "level": "",
                            "service": "",
                            "request_id": ""
                        }
                    }
                ]
            }
        ]
    }
    
    monitoring_dir = Path("monitoring")
    monitoring_dir.mkdir(exist_ok=True)
    
    with open(monitoring_dir / "promtail-config.yml", "w") as f:
        import yaml
        yaml.dump(promtail_config, f, default_flow_style=False)
    
    print("✅ Created Promtail configuration")

def create_alerting_rules():
    """Create Prometheus alerting rules"""
    
    alerting_rules = {
        "groups": [
            {
                "name": "blinkit-alerts",
                "rules": [
                    {
                        "alert": "HighErrorRate",
                        "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) > 0.1",
                        "for": "2m",
                        "labels": {
                            "severity": "critical"
                        },
                        "annotations": {
                            "summary": "High error rate detected",
                            "description": "Error rate is above 10% for {{ $labels.service }}"
                        }
                    },
                    {
                        "alert": "HighResponseTime",
                        "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1",
                        "for": "5m",
                        "labels": {
                            "severity": "warning"
                        },
                        "annotations": {
                            "summary": "High response time detected",
                            "description": "95th percentile response time is above 1s for {{ $labels.service }}"
                        }
                    },
                    {
                        "alert": "ServiceDown",
                        "expr": "up == 0",
                        "for": "1m",
                        "labels": {
                            "severity": "critical"
                        },
                        "annotations": {
                            "summary": "Service is down",
                            "description": "{{ $labels.job }} has been down for more than 1 minute"
                        }
                    },
                    {
                        "alert": "HealthCheckFailing",
                        "expr": "probe_success == 0",
                        "for": "2m",
                        "labels": {
                            "severity": "warning"
                        },
                        "annotations": {
                            "summary": "Health check failing",
                            "description": "Health check for {{ $labels.instance }} has been failing"
                        }
                    }
                ]
            }
        ]
    }
    
    monitoring_dir = Path("monitoring")
    monitoring_dir.mkdir(exist_ok=True)
    
    with open(monitoring_dir / "alert-rules.yml", "w") as f:
        import yaml
        yaml.dump(alerting_rules, f, default_flow_style=False)
    
    print("✅ Created alerting rules")

def create_monitoring_readme():
    """Create README for monitoring setup"""
    
    readme_content = """# Blinkit Clone - Monitoring and Observability

This directory contains the monitoring and observability setup for the Blinkit clone application.

## Components

### Prometheus
- **Port**: 9090
- **Purpose**: Metrics collection and alerting
- **Config**: `prometheus.yml`

### Grafana
- **Port**: 3000
- **Purpose**: Metrics visualization and dashboards
- **Default Login**: admin/admin123
- **Dashboard**: Pre-configured Blinkit monitoring dashboard

### Loki
- **Port**: 3100
- **Purpose**: Log aggregation and storage
- **Integration**: Works with Grafana for log visualization

### Promtail
- **Purpose**: Log shipping to Loki
- **Config**: `promtail-config.yml`
- **Logs Path**: `../logs/*.log`

## Quick Start

1. **Start the monitoring stack**:
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

2. **Access Grafana**:
   - URL: http://localhost:3000
   - Login: admin/admin123
   - Import the Blinkit dashboard

3. **Access Prometheus**:
   - URL: http://localhost:9090
   - View metrics and alerts

## Health Check Endpoints

All services now provide comprehensive health check endpoints:

- `GET /health` - Basic health status
- `GET /health/detailed` - Detailed health with dependencies
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

## Metrics Endpoints

- `GET /metrics` - Prometheus metrics (JSON format)
- `GET /metrics/prometheus` - Prometheus metrics (text format)

## Log Structure

All services now use structured JSON logging with the following fields:

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "service_name": "auth-service",
  "message": "Request completed",
  "request_id": "uuid-here",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "duration_ms": 15.5,
  "client_ip": "127.0.0.1"
}
```

## Alerting

Prometheus alerting rules are configured for:

- High error rates (>10% 5xx responses)
- High response times (>1s 95th percentile)
- Service downtime
- Health check failures

## Correlation IDs

All requests are tracked with correlation IDs for distributed tracing:

- Generated automatically for each request
- Included in all log entries
- Returned in response headers as `X-Request-ID`

## Performance Monitoring

Key metrics tracked:

- Request rate (requests/second)
- Response time percentiles (50th, 95th, 99th)
- Error rates by service and endpoint
- Active request count
- Database query performance
- External service response times

## Troubleshooting

### Common Issues

1. **Logs not appearing in Loki**:
   - Check Promtail configuration
   - Verify log file permissions
   - Ensure log directory exists

2. **Metrics not showing in Prometheus**:
   - Verify service endpoints are accessible
   - Check Prometheus targets status
   - Ensure services are exposing `/metrics`

3. **Health checks failing**:
   - Check service dependencies (database, Redis, etc.)
   - Verify network connectivity
   - Review service logs for errors

### Log Locations

- Main application: `logs/main_application.log`
- API Gateway: `logs/api-gateway.log`
- Auth Service: `logs/auth-service.log`
- Product Service: `logs/product-service.log`
- Cart Service: `logs/cart-service.log`
- Order Service: `logs/order-service.log`
- Delivery Service: `logs/delivery-service.log`
- Notification Service: `logs/notification-service.log`

## Production Considerations

1. **Log Retention**: Configure appropriate log retention policies
2. **Metrics Storage**: Set up long-term metrics storage
3. **Alerting**: Configure alert notifications (email, Slack, etc.)
4. **Security**: Secure monitoring endpoints in production
5. **Scaling**: Consider horizontal scaling for high-traffic scenarios

## Next Steps

1. Set up alert notifications
2. Configure log retention policies
3. Add custom business metrics
4. Implement distributed tracing with Jaeger
5. Set up automated monitoring tests
"""

    monitoring_dir = Path("monitoring")
    monitoring_dir.mkdir(exist_ok=True)
    
    with open(monitoring_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ Created monitoring README")

def main():
    """Main setup function"""
    print("🔧 Setting up monitoring and observability...")
    
    try:
        import yaml
    except ImportError:
        print("❌ PyYAML is required. Install with: pip install PyYAML")
        return
    
    # Create all monitoring configurations
    create_prometheus_config()
    create_grafana_dashboard()
    create_docker_compose_monitoring()
    create_promtail_config()
    create_alerting_rules()
    create_monitoring_readme()
    
    print("\n🎉 Monitoring setup complete!")
    print("\n📋 Next steps:")
    print("1. Start monitoring stack: docker-compose -f monitoring/docker-compose.monitoring.yml up -d")
    print("2. Access Grafana: http://localhost:3000 (admin/admin123)")
    print("3. Access Prometheus: http://localhost:9090")
    print("4. Check service health: curl http://localhost:8000/health/detailed")
    print("\n📁 Files created in ./monitoring/ directory")

if __name__ == "__main__":
    main()