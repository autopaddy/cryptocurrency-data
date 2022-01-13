TAG=manifestgen
VERSION=1.0
ROOTDIR=/data

.PHONY: build
build:
	podman build . -t $(TAG):$(VERSION)

.PHONY: run
run:
	podman run -ti --rm -v ./:$(ROOTDIR) $(TAG):$(VERSION) /bin/ash -c "cd $(ROOTDIR) && CMC_API_KEY=$(CMC_API_KEY) python $(ROOTDIR)/generate.py"
