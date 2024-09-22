#!/usr/bin/env zsh

# Define the command to start the server
start_server="jupyter kernelgateway --KernelGatewayApp.api='kernel_gateway.notebook_http' --KernelGatewayApp.seed_uri='api.ipynb' --KernelGatewayApp.allow_origin='*' --KernelGatewayApp.allow_methods='GET,POST,PUT,DELETE,OPTIONS'"

# Define the command to start the client
start_client="yarn --cwd client build:watch"

# Start the server and the client in the background
eval "${start_server} &"
eval "${start_client} &"

# Keep the script running
wait
