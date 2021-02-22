PKG=rh411
VER=`cat version`

dep: lib
	mkdir -p lib;\
    pip install --target=. Alfred-Workflow; \
    pip install --target=lib -r requirements.txt

build:
	zip -r ../$(PKG)-$(VER).alfredworkflow *

install:
	open ../$(PKG)-$(VER).alfredworkflow


