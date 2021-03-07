PKG=rh411
VER=`cat version`

dep: lib
    pip install --target=. Alfred-Workflow; \
    pip install --target=lib -r requirements.txt

lib:
	mkdir -p lib

clean:
	rm -rf lib workflow

build:
	zip -r ../$(PKG)-$(VER).alfredworkflow *

install:
	open ../$(PKG)-$(VER).alfredworkflow


