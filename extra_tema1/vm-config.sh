#!/bin/bash

BASE_VM="base"
DEFAULT_CONFIG_FILE="default-config.vm"
SHARED_FOLDER_GUEST_NAME="config"

load()
{
    filename=$1
    source ./${filename}
}

deploy()
{
    hostname=$1
    config_file="${hostname}.vm"

    cpus=1
    cpuexecutioncap=100
    memory=1024

    if [[ ! -e "${config_file}" ]]; then
        config_file=${DEFAULT_CONFIG_FILE}
    fi

    ok= load "${config_file}"

    shared_folder_host_path="shared_${hostname}"

    ok= ${ok} && mkdir "${shared_folder_host_path}"
    ok= ${ok} && cp "${config_file}" "${shared_folder_host_path}/config.vm"

    shared_folder_host_path="$(realpath ${shared_folder_host_path})"

    ok= ${ok} && vboxmanage clonevm --name "${hostname}" --register "${BASE_VM}"
    ok= ${ok} && vboxmanage modifyvm "${hostname}" --memory ${memory} --cpus ${cpus} --cpuexecutioncap ${cpuexecutioncap}
    ok= ${ok} && vboxmanage sharedfolder add "${hostname}" --name ${SHARED_FOLDER_GUEST_NAME} \
                                              --hostpath ${shared_folder_host_path} \
                                              --readonly \
                                              --automount
    return ${ok}
}

halt()
{
    hostname=$1
    vboxmanage controlvm "${hostname}" poweroff
}

start()
{
    hostname=$1
    vboxmanage startvm "${hostname}"
}

destroy()
{
    hostname=$1
    vboxmanage unregistervm --delete "${hostname}"
    rm -rf "shared_${hostname}"
}

list()
{
    vboxmanage list vms
}

list_running()
{
    vboxmanage list runningvms
}

usage() 
{
    echo "Usage:"
    echo "$(basename $0) <action> <hostname>"
    echo "action can be \"deploy\", \"halt\", \"start\", \"destroy\", \"list\" or \"listrunning\""
}

if [[ $# -ne 2 ]]; then
    usage
    exit 1
fi

case $1 in
    deploy)
        shift
        deploy "$@"
        ;;
    halt)
        shift
        halt "$@"
        ;;
    start)
        shift
        start "$@"
        ;;
    destroy)
        shift
        destroy "$@"
        ;;
    list)
        shift
        list "$@"
        ;;
    listrunning)
        shift
        list_running "$@"
        ;;
    *)
        usage
        exit 1
esac



