#!/bin/bash

# Copyright (c) 2013 Piotr Banaszkiewicz.
# MIT License, see:
#  https://github.com/pbanaszkiewicz/ganeti_webmgr-setup/blob/master/LICENSE

# This script:
#
# 1. detects user's operating system (Debian or CentOS)
#
# 2. installs system dependencies (Python, ``python-virtualenv``) via user's OS
#    default package managers (``apt`` or ``yum``) [requires ``sudo``]
#
# 3. creates virtual environment in local directory (or in directory specified
#    by user)
#
# 4. installs newest ``pip`` and ``setuptools`` in that virtual environment
#    (they're needed for ``wheel`` packages below)
#
# 5. installs GWM dependencies into that virtual environment. (On Centos and
#    Debian, all of them will be provided as ``wheel`` binary packages, because
#    GWM users might not be allowed to have ``gcc`` & co. installed)
#
# 6. installs GWM itself into that virtual environment
#
# 7. creates configuration directory near that virtual environment with sane
#    default settings in there and random ``SECRET_KEY``
#
# 8. generates proper WSGI file for the project (that can work with custom
#    directory and virtual environment)

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

version="0.11.2" # current version of GWM

# default values
install_directory='/opt/ganeti_webmgr'
config_dir='/opt/ganeti_webmgr/config'
base_url="http://ftp.osuosl.org/pub/osl/ganeti-webmgr/$version"
script_location=$(dirname $0)
gwm_location="$script_location/.."

# helper function: display help message
usage() {
echo "Install (or upgrade) Ganeti Web Manager from OSUOSL servers.

Usage:
    $0 -h
    $0 [-d <dir>] [-D <database>] [-N] [-w <address>]
    $0 -u [<dir>]

Default installation directory:     $install_directory
Default database server:            SQLite
Default remote wheels location:     $base_url
Default config directory:           $config_dir

Options:
  -h                            Show this screen.
  -d <install directory>        Specify install directory.
  -D <database server>          Either 'postgresql' or 'mysql' or 'sqlite'.
                                This option will try to install required
                                dependencies for selected database server
                                (unless -N).  If you don't specify it, SQLite
                                will be assumed the default DB.
  -N                            Don't try to install system dependencies.
  -p <http proxy url>           Make pip use the HTTP proxy specified
  -w <wheels (local/remote) directory location>
                                Where wheel packages are stored.  Don't change
                                this value unless you know what you're doing!
  -u <install directory>        Upgrade existing installation. Forces -N.
                                If you do not provide <install directory> then
                                it assumes the default install directory."
    exit 0
}

# helper: architecture and OS recognizing
lsb_release='/usr/bin/lsb_release'
architecture=`uname -m`
os='unknown'

if [ -x "$lsb_release" ]; then
    # we pull in default values, should work for both Debian and Ubuntu
    os=`$lsb_release -s -i | tr "[:upper:]" "[:lower:]"`

    if [ "$OS" == "centos" ]; then
        os_codename=`$lsb_release -s -r | sed -e 's/\..*//'`
        # we only care about the major version
        os_codename=`echo $os_codename | cut -d . -f 1`
    else
        os_codename=`$lsb_release -s -c | tr "[:upper:]" "[:lower:]"`
    fi

elif [ -r "/etc/redhat-release" ]; then
    # it's either RHEL or CentOS, both is fine
    os='centos'

    # instead of codename, we pull in release version ('6.3', '6.4', etc)
    os_codename=`sed s/.*release\ // /etc/redhat-release | sed s/\ .*//`
    # we only care about the major version
    os_codename=`echo $os_codename | cut -d . -f 1`
fi

#------------------------------------------------------------------------------

no_dependencies=0
upgrade=0
database_server='sqlite'
pip_proxy=""

### Runtime arguments and help text
while getopts "hud:D:Nw:p:" opt; do
    case $opt in
        h)
            usage
            ;;

        u)
            upgrade=1
            if [ -z "$OPTARG" ]; then
                install_directory="$install_directory"
            else
                install_directory="$OPTARG"
            fi
            no_dependencies=1
            ;;

        d)
            install_directory="$OPTARG"
            ;;

        D)
            database="$OPTARG"
            echo "$database" | grep -e '^postgres' -i 1>/dev/null
            if [ $? -eq 0 ]; then
                database_server='postgresql'
            fi
            echo "$database" | grep -e '^mysql' -i 1>/dev/null
            if [ $? -eq 0 ]; then
                database_server='mysql'
            fi
            ;;

        N)
            no_dependencies=1
            ;;

        w)
            base_url="$OPTARG"
            ;;

        p)
            $pip_proxy="--proxy=$OPTARG"
            ;;

        \?)
            # unknown parameter
            exit 2
            ;;
    esac
done

#------------------------------------------------------------------------------

### whether we should try to install system dependencies
if [ $no_dependencies -eq 0 ]; then

    case $os in
        debian)
            package_manager='apt-get'
            package_manager_cmds='install -y'
            check_if_exists "/usr/bin/$package_manager"
            ;;

        ubuntu)
            package_manager='apt-get'
            package_manager_cmds='install -y'
            check_if_exists "/usr/bin/$package_manager"
            ;;

        centos)
            package_manager='yum'
            package_manager_cmds='install -y'
            check_if_exists "/usr/bin/$package_manager"
            ;;
        unknown)
            # unknown Linux distribution
            echo "${txtboldred}Unknown distribution! Cannot install required" \
                 "dependencies!"
            echo "Please install on your own:"
            echo "- Python (version 2.6.x or 2.7.x)"
            echo "- python-virtualenv"
            echo "...and run setup suppressing installation of required deps:"
            echo "  $0 -N ${txtreset}"
            exit 3
            ;;
    esac

    echo ""
    echo "------------------------------------------------------------------------"
    echo "Detected package manager: $package_manager"
    echo "Installing system dependencies.  ${txtboldblue}Please enter your"
    echo "password and confirm installation.${txtreset}"
    echo "------------------------------------------------------------------------"

    ### installing system dependencies
    sudo="/usr/bin/sudo"
    check_if_exists "$sudo"

    # debian based && postgresql
    if [ \( "$os" == "ubuntu" -o "$os" == "debian" \) -a "$database_server" == "postgresql" ]; then
        database_requirements='libpq5'

    # debian based && mysql
    elif [ \( "$os" == "ubuntu" -o "$os" == "debian" \) -a "$database_server" == "mysql" ]; then
        database_requirements='libmysqlclient20'

    # RHEL based && postgresql
    elif [ \( "$os" == "centos" \) -a "$database_server" == "postgresql" ]; then
        database_requirements='postgresql-libs'

    # RHEL based && mysql
    elif [ \( "$os" == "centos" \) -a "$database_server" == "mysql" ]; then
        database_requirements='mysql-libs'
    fi

    ${sudo} ${package_manager} ${package_manager_cmds} \
        python python-virtualenv python-pip ${database_requirements}

    # check whether installation succeeded
    if [ ! $? -eq 0 ]; then
        echo "${txtboldred}Something went wrong. Please install these" \
             "required dependencies on your"
        echo "own:"
        echo "- Python (version 2.6.x or 2.7.x)"
        echo "- python-virtualenv"
        if [ ! -n $database_requirements ]; then
            echo "- $database_requirements"
        fi
        echo "and suppress installing them via -N runtime argument.${txtreset}"
        exit 4
    fi
fi

echo ""
echo "------------------------------------------------------------------------"
echo "Creating virtual environment for Python packages"
echo "------------------------------------------------------------------------"

### creating virtual environment
venv='/usr/bin/virtualenv'
check_if_exists "$venv"

# installing fresh
if [ $upgrade -eq 0 ]; then
    echo "Installing to: $install_directory"

    ${sudo} ${venv} --no-site-packages "$install_directory"
    echo "Ran venv."
    # check if virtualenv has succeeded
    if [ ! $? -eq 0 ]; then
        echo "${txtboldred}Something went wrong. Could not create virtual" \
             "environment"
        echo "in this path:"
        echo "  $install_directory${txtreset}"
        echo "Please create virtual environment manually by using virtualenv" \
             "command."
        exit 5
    fi

# nope! upgrading!
else
    echo "Upgrading: $install_directory"

    # Nothing to do here.  Using pip in a right way handles upgrading
    # automatically.
fi

### first install a local setuptools to bootstrap everything
python="/usr/bin/python"
${python} -m ensurepip --user
echo

### then install pip, which depends on setuptools, and can install the rest
pip="$install_directory/bin/pip"
check_if_exists "$pip"
${sudo} ${pip} install ${pip_proxy} --upgrade pip
echo

### then install all of the dependencies of setuptools, which are cyclic
${sudo} ${pip} install ${pip_proxy} --upgrade appdirs six pyparsing packaging
echo

### setuptools to the newest version, installing wheel
${sudo} ${pip} install $pip_proxy --upgrade setuptools wheel
echo

# check if successfully upgraded pip and setuptools
if [ ! $? -eq 0 ]; then
    echo "${txtboldred}Something went wrong. Could not upgrade pip nor" \
         "setuptools"
    echo "in this virtual environment:"
    echo "  $install_directory${txtreset}"
    echo "Please upgrade pip and setuptools manually by issuing this" \
         "command:"
    echo "  ${pip} install --upgrade setuptools pip"
    exit 5
fi

echo ""
echo "------------------------------------------------------------------------"
echo "Installing Ganeti Web Manager and its dependencies"
echo "------------------------------------------------------------------------"

# WARNING: watch out for double slashes when concatenating these strings!
url="$base_url/$os/$os_codename/$architecture/"

${sudo} ${pip} install $pip_proxy --upgrade --use-wheel --trusted-host ftp.osuosl.org --find-link="$url" "$gwm_location"

if [ ! $? -eq 0 ]; then
    echo "${txtboldred}Something went wrong. Could not install GWM nor its" \
         "dependencies"
    echo "in this virtual environment:"
    echo "  $install_directory${txtreset}"
    echo "Please refer to the official GWM documentation for assistance:"
    echo "  http://ganeti-webmgr.readthedocs.org/en/latest/"
    exit 6
fi

# install dependencies for database
if [ "$database_server" != "sqlite" ]; then
    case $database_server in
        postgresql)
            ${sudo} ${pip} install $pip_proxy --upgrade --use-wheel --trusted-host ftp.osuosl.org --find-link="$url" psycopg2
            ;;
        mysql)
            ${sudo} ${pip} install $pip_proxy --upgrade --use-wheel --trusted-host ftp.osuosl.org --find-link="$url" MySQL-python
            ;;
    esac

    if [ ! $? -eq 0 ]; then
        echo "${txtboldred}Something went wrong. Could not install database" \
            "dependencies"
        echo "in this virtual environment:"
        echo "  $install_directory${txtreset}"
        echo "Please check if you have internet access and consult with official" \
             "GWM documentation:"
        echo "  http://ganeti-webmgr.readthedocs.org/en/latest/"
        exit 7
    fi
fi

# check the environment variable to see if we should use that
if [ -n "$GWM_CONFIG_DIR" ]; then
    config_dir="$GWM_CONFIG_DIR"
fi

# make the config directory if it doesn't exist.
if [ -d "$config_dir" ]; then
    echo "Config directory at $config_dir already exists, not creating it."
else
    echo "Config directory at $config_dir doesn't exist. Creating it."
    ${sudo} mkdir -p "$config_dir"

    if [ ! $? -eq 0 ]; then
        echo "Unable to make default config directory at "
        echo "$config_dir${textreset}"
    fi
fi
