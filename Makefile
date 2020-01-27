
IMAGE_REGISTRY ?= infoblox

APP_NAME := migrate-safe

DOCKERFILE = Dockerfile

GIT_COMMIT := $(shell git log -1 --pretty=format:%h)

ifeq ($(RELEASE_IMAGE_VERSION),)
  IMAGE_VERSION := $(shell date +%Y%m%d)-$(GIT_COMMIT)
else
  IMAGE_VERSION := $(RELEASE_IMAGE_VERSION)
endif

IMAGE_NAME := $(IMAGE_REGISTRY)/$(APP_NAME):$(IMAGE_VERSION)

.PHONY: image push show-image-names show-image-version build main

main: image

build:

image: build
	docker build -f $(DOCKERFILE) -t $(IMAGE_NAME) .
	docker image tag $(IMAGE_NAME) $(IMAGE_REGISTRY)/$(APP_NAME):latest

push: image
	docker push $(IMAGE_NAME)

push-latest: image
	docker push $(IMAGE_REGISTRY)/$(APP_NAME):latest

show-image-names:
	@echo $(APP_NAME)

show-image-version:
	@echo $(IMAGE_VERSION)

binaries:
	tools/make-patchelf.sh
	tools/get-binaries.sh

check.pre:
	tools/env-test.sh bin/migrator-dbtool.py pre
check.pre-force:
	tools/env-test.sh bin/migrator-dbtool.py pre-force
check.post:
	tools/env-test.sh bin/migrator-dbtool.py post

intel:
	env DATABASE_FORCE=false tools/env-test.sh bin/intel-migrator.sh

intel-force:
	env DATABASE_FORCE=true tools/env-test.sh bin/intel-migrator.sh
