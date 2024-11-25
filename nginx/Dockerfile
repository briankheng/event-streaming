FROM openresty/openresty:latest

RUN apt-get update && apt-get install -y openresty-opm luarocks git \
	&& luarocks install lua-resty-kafka && luarocks install lua-resty-http
