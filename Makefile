.PHONY: demo

demo:
	@echo "Starting demo stack via docker compose..."
	@docker compose up --build -d
	@sleep 5
	@echo "Running end-to-end quick demo script..."
	@python scripts/run_quick_demo_e2e.py
	@echo "Shutting down demo stack..."
	@docker compose down
