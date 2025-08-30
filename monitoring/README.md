# Blinkit Clone - Monitoring and Observability

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
