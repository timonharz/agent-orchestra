#!/bin/bash

# Docker management script for OpenManus API

# Make script executable with:
# chmod +x docker-run.sh

case "$1" in
  start)
    echo "Building and starting containers..."
    docker-compose up -d
    echo "Containers started. View logs with: ./docker-run.sh logs"
    ;;
  stop)
    echo "Stopping containers..."
    docker-compose down
    ;;
  restart)
    echo "Restarting containers..."
    docker-compose down
    docker-compose up -d
    ;;
  logs)
    echo "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
    ;;
  build)
    echo "Rebuilding containers..."
    docker-compose build
    ;;
  rebuild)
    echo "Rebuilding and starting containers..."
    docker-compose down
    docker-compose build
    docker-compose up -d
    ;;
  shell)
    echo "Opening shell in the API container..."
    docker-compose exec api bash
    ;;
  status)
    echo "Container status:"
    docker-compose ps
    ;;
  *)
    echo "OpenManus API Docker Helper"
    echo "Usage: $0 {start|stop|restart|logs|build|rebuild|shell|status}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the containers"
    echo "  stop     - Stop the containers"
    echo "  restart  - Restart the containers"
    echo "  logs     - Show container logs"
    echo "  build    - Rebuild the containers"
    echo "  rebuild  - Rebuild and restart the containers"
    echo "  shell    - Open a shell in the API container"
    echo "  status   - Show container status"
    exit 1
esac

exit 0
