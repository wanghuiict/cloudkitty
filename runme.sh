#!/bin/bash

DIST="cloudkitty-11.1.0-py2-none-any.whl"

if [ $# -eq 0 ]; then
    echo -e "Usage:"
    echo -e "    $0 build|deploy|clean|distclean"
    echo -e "    $0 deploy [cloudkitty_api cloudkitty_processor] (default)"
    echo -e "    $0 deploy cloudkitty_api"
    echo -e "    $0 deploy cloudkitty_processor" 
    exit 0
fi

if [ "$1" == "build" ] ;then
    python setup.py bdist_wheel
    exit $?
elif [ "$1" == "deploy" ] ;then
    shift
elif [ "$1" == "clean" ] ;then
    python setup.py clean
elif [ "$1" == "distclean" ] ;then
    python setup.py clean
    pushd dist/ && rm -f ./* && popd
    exit $?
else
    echo "error input"
    exit -1
fi

if [ ! -z "$1" ]; then
    i=0
    for x in $* ; do
        containers[$i]=$x
        ((i++))
    done
else
    containers=(cloudkitty_api cloudkitty_processor)
fi

for x in ${containers[@]};do
    echo $x
    docker cp dist/$DIST $x:/ && docker exec -it -u root $x bin/bash -c "pip install --force-reinstall --no-deps $DIST && rm -f $DIST" && docker restart $x
    echo "docker ps |grep cloudkitty"
    docker ps |grep cloudkitty
done

