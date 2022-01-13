FROM python:alpine3.14

# Install ImageMagick ( Used for Icon processing )
RUN apk add --no-cache imagemagick curl

RUN pip3 install requests
