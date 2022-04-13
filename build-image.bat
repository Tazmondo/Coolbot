docker buildx build -t tazmondo/coolbot --platform linux/amd64,linux/arm64 --push .
docker pull tazmondo/coolbot
