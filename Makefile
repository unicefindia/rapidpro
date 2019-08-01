#RapidPro docker build management
.PHONY: build release 

all: build release 

build:	
	docker build -t $(REGISTRY)/$(IMAGE):$(BUILD_NUMBER) .
release: 
	docker push $(REGISTRY)/$(IMAGE):$(BUILD_NUMBER)

