build:
	podman build -f Dockerfile-service -t sony-nre-testwork-testservice .
	
run:
	podman run -dp 8080:5000 --name myapi -e PROC_NUM=4 -v routes.txt:/testwork/routes.txt sony-nre-testwork-testservice

remove:
	podman stop myapi
	podman rm myapi

removeimg:
	podman rmi -f sony-nre-testwork-testservice