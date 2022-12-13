build:
	podman build -f Dockerfile-service -t sony-nre-testwork-testservice .

run:
	podman run -dp 8080:5000 --name myapi -v routes.txt:/testwork/service/routes.txt sony-nre-testwork-testservice

remove:
	podman stop myapi
	podman rm myapi

removeimg:
	podman rmi -f sony-nre-testwork-testservice