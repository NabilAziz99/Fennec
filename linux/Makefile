IMAGE_NAME = fennec-linux:latest

.PHONY: build rebuild clean status

# Normal build (uses cache)
build:
	docker build -t $(IMAGE_NAME) .

# Force rebuild without cache
rebuild:
	docker build --no-cache -t $(IMAGE_NAME) .

# Remove image and rebuild fresh
clean:
	-docker rmi -f $(IMAGE_NAME) 2>/dev/null || true
	docker build --no-cache -t $(IMAGE_NAME) .

# Show image status
status:
	@echo "=== Fennec Linux Image Status ==="
	@docker image inspect $(IMAGE_NAME) --format 'ID: {{.Id}}' 2>/dev/null || echo "Image not found"
	@docker image inspect $(IMAGE_NAME) --format 'Created: {{.Created}}' 2>/dev/null || true
	@docker image inspect $(IMAGE_NAME) --format 'Size: {{.Size}} bytes' 2>/dev/null || true