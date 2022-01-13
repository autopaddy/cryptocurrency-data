TAG=manifestgen
VERSION=1.0
ROOTDIR=/data

.PHONY: build
build:
	podman build . -t $(TAG):$(VERSION)

.PHONY: run
run:
	podman run -ti --rm -e CMC_API_KEY=$(CMC_API_KEY) -v ./:$(ROOTDIR) $(TAG):$(VERSION) /bin/ash -c "cd $(ROOTDIR) && python $(ROOTDIR)/generate.py"
