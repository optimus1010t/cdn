.PHONY: clean run-client run-edge

clean:
	@echo "Cleaning client_content/ and edge_cache/"
	rm -rf client_content/* edge_cache/* origin_content/* new_files.txt files_list.txt new_files_while_replicating.txt

client:
	clear
	@echo "Running client.py"
	python3 client.py

edge:
	clear
	@echo "Running edge.py"
	python3 edge.py

origin:
	clear
	@echo "Running the 1 origin servers"
	cd origin1 && python3 ../origin.py --port 5000 &
	cd origin2 && python3 ../origin.py --port 5001 &
	cd origin3 && python3 ../origin.py --port 5002 &

provider:
	clear
	@echo "Running provider.py"
	python3 provider.py

dns:
	clear
	@echo "Running dns.py"
	python3 dns.py

kill_origins:
	@echo "Killing all origin servers"
	kill -9 $(shell lsof -t -i:5000) $(shell lsof -t -i:5001) $(shell lsof -t -i:5002) 2>/dev/null || true
	@echo "All origin servers killed"
