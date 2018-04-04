#!/bin/bash

redirect_output()
{
    local OUTPUT_FILE="/var/log/system-bootstrap.log"

    exec 3>&1 4>&2 &>>$OUTPUT_FILE
}

restore_output()
{
    exec 1>&3 2>&4
}

begin_message()
{
    now=$(date +"%d/%m/%Y, %H:%m:%S")

    echo "--------------------------------------------------------------"
    echo $now
    echo "--------------------------------------------------------------"
}

install_basic()
{
    yum update -y
    yum install vim -y
    yum install git -y
}

setup_network()
{
    CONN="enp0s8"
    IP="192.168.56.101/24"

    declare -A settings=(
        ["ipv4.method"]="manual"
        ["ipv4.addresses"]="$IP"
    )

    for key in ${!settings[@]}; do
        val=${settings[$key]}

        ok= nmcli con mod $CONN $key $val

        if [[ ${ok} -ne 0 ]]; then
            break
        fi
    done

    ok= $ok && nmcli con down $CONN
    ok= $ok && nmcli con up   $CONN

    return $ok
}

set_attribute()
{
    local key=$1
    local sep=$2
    local val=$3
    local file=$4

    if grep -q "^[^#]\?$key$sep" $file; then
        sed -i "s/^[^#]\?$key$sep.*/$key$sep$val/g" $file  
    else
        echo "$key$sep$val" >> $file 
    fi

    return 0
}

setup_rsa()
{
    echo $HOME
    yes "" | ssh-keygen -t rsa -N ""
}

setup_ssh()
{
    local FILE="/etc/ssh/sshd_config"
    
    local key_1="ChallengeResponseAuthentication"
    local val_1="no"

    local key_2="PasswordAuthentication"
    local val_2="no"
    
    local ok

    ok=        set_attribute $key_1 " " $val_1 $FILE
    ok= $ok && set_attribute $key_2 " " $val_2 $FILE
    ok= $ok && setup_rsa $FILE

    return $ok
}

setup_selinux()
{
    local FILE="/etc/selinux/config"
    local ok

    ok=        set_attribute "SELINUX" "=" "disabled" $FILE
    ok= $ok && setenforce 0
    
    return $ok
}

redirect_output

begin_message

ok=        install_basic
ok= $ok && setup_network
ok= $ok && setup_ssh
ok= $ok && setup_selinux

if $ok ; then
    echo "Success!"
else
    echo "Failure!"
fi

restore_output

