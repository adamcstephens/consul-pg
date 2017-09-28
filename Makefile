all:

up:
	docker-compose up -d && docker-compose logs -f --tail=10 dc1agent1 dc1agent2 dc2agent1

webui:
	open http://localhost:8500
