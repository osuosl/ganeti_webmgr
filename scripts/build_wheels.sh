#!/bin/bash

# Copyright (c) 2013 Piotr Banaszkiewicz.
# MIT License, see:
#  https://github.com/pbanaszkiewicz/ganeti_webmgr-setup/blob/master/LICENSE

# This script builds Python wheel packages to the specified directory from
# within a virtual environment

# default paths
env_dir='./venv'
wheels_dir='./wheels'
script_location=$(dirname $0)
gwm_location="$script_location/.."

# helpers: setting text colors
txtbold=$(tput bold)
txtred=$(tput setaf 1)
txtgreen=$(tput setaf 2)
txtblue=$(tput setaf 4)
txtwhite=$(tput setaf 7)
txtboldred=${txtbold}$(tput setaf 1)
txtboldgreen=${txtbold}$(tput setaf 2)
txtboldblue=$(tput setaf 4)
txtboldwhite=${txtbold}$(tput setaf 7)
txtreset=$(tput sgr0)

# helper function: check if some binary exists and is callable and otherwise
# echo warning
check_if_exists() {
    if [ ! -x $1 ]; then
        echo "${txtboldred}Cannot find $1! It's necessary to complete" \
             "installation.${txtreset}"
        exit 1
    fi
}

# helper function: display help message
usage() {
echo "Build Ganeti Web Manager dependencies as wheel packages.

Usage:
    $0 -h
    $0 [-e <dir>] [-w <dir>] [-N]

Default virtual environment path:   $env_dir
Default wheels output directory:    $wheels_dir

Wheels are put in subfolders in this pattern:
    $wheels_dir/{distribution}/{version}/{architecture}/

Options:
  -h                        Show this screen.
  -e <environment dir>      Specify virtual environment path. This gets erased
                            on every runtime.
  -w <wheels dir>           Where to put built wheel packages.
  -N                        Skip installing system dependencies."
    exit 0
}

# helper: architecture and OS recognizing
lsb_release='/usr/bin/lsb_release'
architecture=`uname -m`
os='unknown'

if [ -x $lsb_release ]; then
    # we pull in default values, should work for both Debian and Ubuntu
    os=`$lsb_release -s -i | tr "[:upper:]" "[:lower:]"`

    if [ "$OS" == "centos" ]; then
        os_codename=`$lsb_release -s -r | sed -e 's/\..*//'`
    else
        os_codename=`$lsb_release -s -c | tr "[:upper:]" "[:lower:]"`
    fi

elif [ -r "/etc/redhat-release" ]; then
    # it's either RHEL or CentOS, which is fine
    os='centos'

    # instead of codename, we pull in release version ('6.3', '6.4', etc)
    os_codename=`sed s/.*release\ // /etc/redhat-release | sed s/\ .*//`
fi

#------------------------------------------------------------------------------

### Runtime arguments and help text
force_gwm_refresh=0
no_dependencies=0
while getopts "he:g:Gb:a:w:N" opt; do
    case $opt in
        h)
            usage
            ;;
        e)
            env_dir="$OPTARG"
            ;;
        w)
            wheels_dir="$OPTARG"
            ;;
        N)
            no_dependencies=1
            ;;

        \?)
            # unknown parameter
            exit 2
            ;;
    esac
done

### instal building dependencies
if [ $no_dependencies -eq 0 ]; then
    case $os in
        debian)
            package_manager='apt-get'
            package_manager_cmds='install -y'
            check_if_exists "/usr/bin/$package_manager"
            database_requirements='libpq-dev libmysqlclient-dev'
            ;;

        ubuntu)
            package_manager='apt-get'
            package_manager_cmds='install -y'
            check_if_exists "/usr/bin/$package_manager"
            database_requirements='libpq-dev libmysqlclient-dev'
            ;;

        centos)
            package_manager='yum'
            package_manager_cmds='install -y'
            check_if_exists "/usr/bin/$package_manager"
            database_requirements='postgresql-devel mysql-devel'
            ;;

        unknown)
            # unknown Linux distribution
            echo "${txtboldred}Unknown distribution! Cannot install required" \
                 "dependencies!"
            echo "Please install on your own:"
            echo "- Python (version 2.6.x or 2.7.x)"
            echo "- python-virtualenv"
            echo "- $database_requirements"
            echo "...and run setup suppressing installation of required deps:"
            echo "  $0 -N ${txtreset}"
            exit 3
            ;;
    esac
fi

sudo="/usr/bin/sudo"
check_if_exists $sudo

# install building dependencies
${sudo} ${package_manager} ${package_manager_cmds} python python-dev \
    python-virtualenv ${database_requirements} git

check_if_exists "/bin/rm"
check_if_exists "/usr/bin/virtualenv"
check_if_exists "/usr/bin/git"

# remove venv
# use force in case rm is aliased to 'rm -i' or something as nasty
/bin/rm "$env_dir" -rf 2>/dev/null

# create venv
/usr/bin/virtualenv --setuptools --no-site-packages "$env_dir"
if [ ! $? -eq 0 ]; then
    echo "${txtboldred}Something went wrong. Could not create virtual" \
         "environment"
    echo "in this path:"
    echo "  $env_dir${txtreset}"
    exit 3
fi

# update pip, setuptools and wheel
pip="$env_dir/bin/pip"
check_if_exists "$pip"
${pip} install --upgrade setuptools pip wheel
if [ ! $? -eq 0 ]; then
    echo "${txtboldred}Something went wrong. Could not install setuptools," \
         "pip or wheel"
    echo "in this virtual environment:"
    echo "  $env_dir${txtreset}"
    exit 4
fi

# install gwm into venv, put wheels to the wheel dir
# WARNING: watch out for that concatenation of string paths!
wheel_path="$wheels_dir/$os/$os_codename/$architecture"
${pip} wheel --log=./pip.log --wheel-dir="$wheel_path" "$gwm_location" \
    psycopg2 MySQL-python
if [ ! $? -eq 0 ]; then
    echo "${txtboldred}Something went wrong. Could not create wheel" \
         "packages."
    echo "Check out pip log to see more:"
    echo "  ./pip.log${txtreset}"
    exit 6
fi

# remove venv
/bin/rm "$env_dir" -r
