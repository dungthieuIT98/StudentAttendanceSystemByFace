.PHONY: help build up down restart logs shell migrate createsuperuser backup clean

help:
	@echo "Available commands:"
	@echo "  make build           - Build Docker images"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make logs            - View logs"
	@echo "  make status          - Show status"
	@echo "  make shell           - Django shell"
	@echo "  make migrate         - Run migrations"
	@echo "  make createsuperuser - Create superuser"
	@echo "  make backup          - Backup database"
	@echo "  make pgadmin         - Start with pgAdmin"
	@echo "  make clean           - Remove all (WARNING!)"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started at http://localhost:8000"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

status:
	docker-compose ps

shell:
	docker-compose exec web python manage.py shell

migrate:
	docker-compose exec web python manage.py migrate

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

backup:
	@echo "Creating backup..."
	docker-compose exec db pg_dump -U postgres face_attendance > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup completed!"

pgadmin:
	docker-compose --profile tools up -d
	@echo "pgAdmin: http://localhost:5050"

clean:
	docker-compose down -v
	@echo "All removed!"
