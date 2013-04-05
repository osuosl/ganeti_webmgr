========
REST API
========

Development of the RESTful API for GWM started as a Google Summer of
Code 2011 project.
The developer, Bojan Suzic, can be reached at bojan.suzic@gmail.com.
The mentor for this project is Peter Krenesky.

The current version of the page describes its status as of ~end August
2011. Currently it supports a fair amount of the underlying
functionality.

Additionally, this page is intented as a development resource and
documentation source for the project.

The project code can be reached at https://github.com/bsu/GWM2.
The additional code (changes in other related modules) can be found at
the following locations:

* https://github.com/bsu/django_obj_perm 
* https://github.com/bsu/django_obj_log.

Users and developers are encouraged to try this addon and send their
suggestions/bug reports/improvements either directly to the author,
using the `GWM mailing list <http://groups.google.com/group/ganeti-webmgr>`_ or 
`issue tracker <http://code.osuosl.org/projects/ganeti-webmgr/issues>`_.
Please put the line ****[REST-API]**** in the subject if you are sending email
message.

REST API for GWM can now be considered as a beta software. For the
further development the following is proposed:

Roadmap:

* completion of unit tests
* relocate parts of endpoints which may contain long answers - that
  variables should be accessed separately (such as object logs)
* further refinement of the code and documentation
* work on further integration (like cloud driver)

The **users/developers/visitors are advised to test** the code and **submit
the comments/notices/wishes**. Comments can be submitted either directly
to the author, here on this wiki or using the `Redmine ticket <http://code.osuosl.org/issues/3573>`_

The version containing significant changes to this version may be
expected in **November 2011**.

About this documentation
------------------------

This documentation covers basic functionality of the REST API. It
consists of the subsections, referring to particular endpoints forming
the API. As an endpoints referred are application resources exposed as
URIs through appropriate hierarchy. Currently, the system exposes the
following resources as REST API endpoints: **User**,
**Group**, **Virtual Machine**, **Cluster**,
**Node**, **Job**. These are accessible in the form of
CRUD operations using HTTP protocol.

By default, each API endpoint returns a list of resources.

For example::

    /api/vm/

would return a list of Virtual Machines in the system, while the
particular VM resource is accessed through::

    /api/vm/1/

where 1 represents identifier of particular Virtual Machine. This way
only that particular resource is returned.
Each resource contains fields related to particular instance in the
system. The field types and their properties are described further in
the documentation, as a part of related subsections.

For each endpoint described is basic scheme of its resource
representation. The scheme includes name, type and description of the
particular fields, Additional properties described are  possibility for
the field to be modified and whether the field returned may be excluded
from the representation e.g. nullable. The later one might be useful for
clients to prevent unexpected behavior.

While **type** field represents basic data types, it should be
noted that **related** type points to other resource in the
system. For example::

    ...
    <cluster>
    ...
    <virtualmachine>
    /api/vm/5
    </virtualmachine>
    </cluster>
    ...

says that particular cluster resource includes virtualmachine
resource, described by related URI. Therefore, if necessary, the
complete resource referred at that point may be obtained through
provided URI.

This documentation trends to provide as much as complete list of
resources and their schematic description. However, due to the level of
deepness and limitations of the current wiki system, in some cases this
representation is simplified and explained in words rather than in
tabular form. It should be noted that all these descriptions are already
included in the system.

Using::

    http://somesite.com/api/?format=xml

user is able to get the list of resources exposed, while with the help of::

    http://somesite.com/api/resource/schema/?format=xml

the system returns detailed schema of resource representation and field
properties in XML format. Therefore, the user is always able to take a
look and check detailed description about a resource, if the one
provided here in documentation is not detailed and clear enough.

Design principles
-----------------

This API aims to expose the resources of Ganeti Web Manager, making
suitable for integration into other systems or just performing of simple
operations on resources. It does not aim to expose all resources and
functions contained in the software, but only the set deemed necessary
in order to support its business functions. Currently, it means that the
most of the functionality present in the web interface is available for
usage and manipulation also using this REST API.

Installation
------------

The most of the code of this addon comes under **/api**
directory of GWM distribution. Other code changes are done in some of
views and dependent modules (like **django_object_log** and
**django_object_permissions**). Its inclusion in the GWM is
done in **/urls.py** via::

    urlpatterns = patterns('',
    ...
        (r'^', include('api.urls')),
    ...

The prerequisite for running RESTful API over Ganeti Web Manager is to
have **django-tastypie** installed. The latest active
version/commit of **tastypie** should be used in order to
support **ApiKeys** based authentication. That means, as of
time of writing this documentation, that **tastypie** should be
installed manually. Additionally, the following line in
**tastypie/authentication.py**::

    username = request.GET.get('username') or request.POST.get('username')

should be changed to::

    username = request.GET.get('username') or request.POST.get('username')
    or request.GET.get('user') or request.POST.get('user')

This is the known issue with **tastypie** already reported in
its bug system. If not changed, the part **username** in
**/api/user/?api_key=xxx&username=xxx** will produce error
message during browsing the main user endpoint. This change makes
**tastypie** to accept **user** for authentication
instead of **username**. Later produces collision with the
field of the same name under **User** model class.

The next change related to the installation of the module is inclusion
of **'tastypie'** in **INSTALLED_APPS** of
**settings.py**. This will produce necessary tables during
installation/migration.

Development
-----------

The code is prepared as a part of GSoC activities, and therefore by
person not being a part of narrowed GWM development team before. As a
such, the main principle to be followed is to try not to interfere too
much with existing code. It implies further that the resulting code
should be considered as an simple to install add-on. The core business
logic of the GWM have not been changed or altered. The most changes done
on GWM code are of technical nature, trying to make functions/views
accessible to REST backend interface additionally. The code has been
committed to separate repository. I tried mostly to perform smaller
commits in size, in order to make the code and changes easily readable
and trackable.

The framework used to introduce RESTful interface is **django-tastypie**.
It has been selected after initial research and testing of several
popular Python/Django/REST frameworks. The system supports both XML and
JSON as input/output serializations.

Authentication and Authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The authentication is done using **API keys**. For each user
the appropriate API key is generated automatically. The key can be
renewed/recreated using **POST** request and appropriate action
inside API. The access to the system looks like in the following
example::

    http://localhost:8000/api/?format=xml&api_key=381a5987a611fb1f8c68ffad49d2cd2b9f92db71&user=test

.. Note:: **username** initially supported by
          **tastypie** has been replaced with **user** in the
          example query above. The changes and reasons are described in the
          installation section of this document.

Authorization is completely dependent on Django's authorization system.
The existing views from the GWM have been used to expose the most of
resources available. Those views are already integrated in Django's
authorization system. Therefore, this API should not contain critical
security flaws or problems and should be easier to maintenance.

REST API endpoints
------------------

/api/user
~~~~~~~~~

This endpoint exposes data and operations related to the user
management.
The following table provides the descriptions of the fields:

.. raw:: html

	<table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>ReadOnly </th>
			<th>Nullable </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>username</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters</td>
		</tr>
		<tr>
			<td><code>ssh_keys</code></td>
			<td><code>list</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>SSH keys for user's account. The list may be composed of several objects.</td>
		</tr>
		<tr>
			<td><code>first_name</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>last_name</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>actions_on_user</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns the actions done on the user. The list is composed of objects, containing elements as described here.</td>
		</tr>
		<tr>
			<td><code>groups</code></td>
			<td><code>related</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns the groups the user is member of</td>
		</tr>
		<tr>
			<td><code>api_key</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns the api key of the user</td>
		</tr>
		<tr>
			<td><code>used_resources</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns the resources used by the objects user has access to in the form of the list.</td>
		</tr>
		<tr>
			<td><code>is_active</code></td>
			<td><code>boolean</code></td>
			<td> </td>
			<td> </td>
			<td>Designates whether this user should be treated as active. Unselect this instead of deleting accounts.</td>
		</tr>
		<tr>
			<td><code>id</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>is_superuser</code></td>
			<td><code>boolean</code></td>
			<td> </td>
			<td> </td>
			<td>Designates that this user has all permissions without explicitly assigning them.</td>
		</tr>
		<tr>
			<td><code>is_staff</code></td>
			<td><code>boolean</code></td>
			<td> </td>
			<td> </td>
			<td>Designates whether the user can log into this admin site.</td>
		</tr>
		<tr>
			<td><code>last_login</code></td>
			<td><code>datetime</code></td>
			<td> </td>
			<td> </td>
			<td>A date &#38; time as a string. Ex: "2010-11-10T03:07:43"</td>
		</tr>
		<tr>
			<td><code>date_joined</code></td>
			<td><code>datetime</code></td>
			<td> </td>
			<td> </td>
			<td>A date &#38; time as a string. Ex: "2010-11-10T03:07:43"</td>
		</tr>
		<tr>
			<td><code>user_actions</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Returns the actions done by the user. The list is composed of objects, containing elements as described here.</td>
		</tr>
		<tr>
			<td><code>permissions</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns the status of users permissions on different families of objects</td>
		</tr>
		<tr>
			<td><code>password</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Returns hashed password</td>
		</tr>
		<tr>
			<td><code>email</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>resource_uri</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
	</table>

Explanations for particular list elements 
'''''''''''''''''''''''''''''''''''''''''

**Container: ssh_keys**

The elements of the list are denoted as **value** nodes,
containing paricular ssh key for the user in the form of **string
hash**

Example::

    <ssh_keys type="list">
    <object type="hash">
    <id type="integer">1</id>
    <key>ssh-rsa
    A398kuwNzaC1yc2EAAAADAQABAAABAQDI2oqyrleSvAg4CV5A/4ZZ2fTEFAYU1W2i8373zspaJCSO0eHIl+v4fGeIzH7CFokbM98ip2mwe7KtFk2VoO1
    /E9ucXR4xcxo77sxGSGH8hiS89aUcHmPKyRYlYj5TwqkZopxYTFmeUhkhP9e5YrlTRXMdhMsIXqXAKRujjySycQ45QLqdYOHbfohU0aKtDN01bYFOQ7/y/9wepXczlXD7rTIhT6
    /aq2vvOoyiGo9vaiIfqbtLjqkjwecDGykesw1c9d07vH53myiLLLkAGGk4KudKSWV6ZxK0ap3/olzzJ3HZpk5MAel5ELX6XuT8VmA3H3Yl5N//DrBUmKciMIaRx
    xxx@gmail.com
    </key>
    </object>
    <object>
    <id type="integer">2</id>
    <key>ssh-rsa
    7398kuwNzaC1yc2EAAAADAQABAAABAQDI2oqyrleSvAg4CVjskajslajwFAYU1W2i8373zspaJCSO0eHIl+v4fGeIzH7CFokbM98ip2mwe7KtFk2VoO1
    /E9ucXR4xcxo77sxGSGH8hiS89aUcHmPKyRYlYj5TwqkZopxYTFmeUhkhP9e5YrlTRXMdhMsIXqXAKRujjySycQ45QLqdYOHbfohU0aKtDN01bYFOQ7/y/9wepXczlXD7rTIhT6
    /aq2vvOoyiGo9vaiIfqbtLjqkjwecDGykesw1c9d07vH53myiLLLkAGGk4KudKSWV6ZxK0ap3/olzzJ3HZpk5MAel5ELX6XuT8VmA3H3Yl5N//DrBUmKciMIYYY
    yyy@gmail.com
    </key>
    </object>
    </ssh_keys>

**Containers: user_actions and actions_on_users**

This is the list of **objects**, each object consisting of
nullable fields denoted as **obj1, obj2, user, action_name**.
The both containers share the representation. The difference between
these is the fact that first describes actions performed by user, while
the second one describes actions performed on user (by administrator,
for instance).
The both containers provide read only information.

.. raw:: html

	<table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>obj1</code>, <code>obj2</code> </td>
			<td> <code>related</code> </td>
			<td> Describe action object</td>
		</tr>
		<tr>
			<td><code>timestamp</code> </td>
			<td> <code>timestamp&gt;</code> </td>
			<td> Date and time of action execution</td>
		</tr>
		<tr>
			<td><code>user</code></td>
			<td><code>related</code></td>
			<td>User performing the action</td>
		</tr>
		<tr>
			<td><code>action_name</code></td>
			<td><code>string</code></td>
			<td>Describes action name using internal descriptions</td>
		</tr>
	</table>

Example::

    <user_actions type="list">
    <object type="hash">
    <obj1>/api/vm/3/</obj1>
    <timestamp>2011-07-31T15:23:45.533479</timestamp>
    <obj2>/api/job/68/</obj2>
    <user>/api/user/2/</user>
    <action_name>VM_REBOOT</action_name>
    </object>
    <object type="hash">
    <obj1>/api/vm/3/</obj1>
    <timestamp>2011-07-31T17:04:02.333061</timestamp>
    <user>/api/user/2/</user>
    <action_name>EDIT</action_name>
    </object>

**Container used_resources**

This list consists of **object** elements, each containing
**resource**, **object** and **type**.
The field **object** represents related resource for which the
system resources consumption is given. The **type** is
**string** describing the object type using internal
descriptions (like **VirtualMachine** for virtual machine).
The **resource** contains subfields **virtual_cpus**,
**disk** and **ram**, each of type
**integer** and representing actual consumption of the
particular system resource in system's default dimension (e.g. MBs for
RAM consumption).

Example::

    <used_resources type="list">
    <object type="hash">
    <resource type="hash">
    <virtual_cpus type="integer">0</virtual_cpus>
    <disk type="integer">0</disk>
    <ram type="integer">0</ram>
    </resource>
    <object>/api/vm/3/</object><
    type>VirtualMachine</type>
    </object>
    <object type="hash">
    <resource type="hash">
    <virtual_cpus type="integer">0</virtual_cpus>
    <disk type="integer">0</disk>
    <ram type="integer">0</ram></resource>
    <object>/api/vm/11/</object>
    <type>VirtualMachine</type>
    </object>
    </used_resources>

**Container permissions**

**Permissions** contains elements describing particular
resource type, each further containing a list of resources. The primary
**elements** are described as **Cluster**,
**VirtualMachine**, **Group**. Their list member main
nodes are described as **object**, containing
**object** reference (related resource) for which the
permissions are set, and the **permissions** list containing
list of **values** as strings, describing permission type in
internal format (like **create_vm**).

Example::

    <permissions type="hash">
    <Cluster type="list"/>
    <Group type="list"/>
    <VirtualMachine type="list">
    <object type="hash">
    <object>/api/vm/3/</object>
    <permissions type="list">
    <value>admin</value>
    <value>power</value>
    <value>tags</value>
    </permissions>
    </object>
    <object type="hash">
    <object>/api/vm/11/</object>
    <permissions type="list">
    <value>admin</value>
    </permissions></object>
    </VirtualMachine>
    </permissions>


Manipulation and operations using POST/PUT/DELETE methods
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

The fields marked as non-readonly (table above) can be subject of
further manipulation and operations. **The same applies to the rest of
the document - those fields can be automatically updated or deleted by
performing analog request.**
In order to maintain consistency with REST approach, the
**PUT** method is used on currently available resources with
purpose to change or update them. On another side, **POST**
method is used either to generate new resources, or to perform
predefined actions on currently existing resources.

The following example demonstrates changing of users lastname and status
in system (disabling its account).
Request URI::

    PUT /api/user/1/?api_key=xxxxx&username=yyyyy

Request header::

    Content-Type: application/json
    Accept: application/json

Request payload::

    {"last_name":"New LastName", "is_active":false}

Server response::

    HTTP/1.1 204 NO CONTENT
    Date: Sat, 06 Aug 2011 11:18:25 GMT
    Server: WSGIServer/0.1 Python/2.7.1+
    Vary: Accept-Language, Cookie
    Content-Length: 0
    Content-Type: text/html; charset=utf-8
    Content-Language: en

The next example demonstrates generating of new Api key for the user:

Request URI::

    POST /api/user/2/?api_key=xxxxx&username=yyyyy

Request header::

    Content-Type: application/json
    Accept: application/xml

Request payload::

    {"action":"generate_api_key"}

Server response::

    HTTP/1.1 201 CREATED
    Date: Sat, 06 Aug 2011 11:21:56 GMT
    Server: WSGIServer/0.1 Python/2.7.1+
    Vary: Accept-Language, Cookie
    Content-Type: text/html; charset=utf-8
    Content-Language: en

Response body::

    <?xml version='1.0' encoding='utf-8'?>
    <object>
    <api_key>de0a57db0ce43d0f3c52f83eaf33387750ac9953</api_key>
    <userid>2</userid>
    </object>

For the API Key manipulation under **/api/user/** endpoint
implemented are two POST actions: **generate_api_key**, as
demonstrated in the example above, and **clean_api_key**.
The former generates a new API key for the user and returns it in the
response, while the later one cleans user's API key. This way its access
to the system using REST API is disabled, but the standard access using
web interface is untouch.

Additionally, two POST actions are implemented for user-group membership
manipulation.

.. raw:: html

	<table>
		<tr>
			<th>Action </th>
			<th>Payload </th>
			<th>Description </th>
			<th>Example </th>
		</tr>
		<tr>
			<td><code>add_to_group</code></td>
			<td><code>group</code></td>
			<td>Add the user to the group</td>
			<td><pre>{'action':'add_to_group', 'group':'/api/group/1/'}</pre></td>
		</tr>
		<tr>
			<td><code>remove_from_group</code></td>
			<td><code>group</code></td>
			<td>Remove the user from the group</td>
			<td><pre>{'action':'remove_from_group', 'group':'/api/group/1/'}</pre></td>
		</tr>
		<tr>
			<td><code>generate_api_key</code></td>
			<td style="text-align:center;">-</td>
			<td>Generate API key for the user </td>
			<td><pre>{'action':'generate_api_key'}</pre></td>
		</tr>
		<tr>
			<td><code>clean_api_key</code></td>
			<td style="text-align:center;">-</td>
			<td>Clean API key for the user </td>
			<td><pre>{'action':'clean_api_key'}</pre></td>
		</tr>
	</table>

/api/group
~~~~~~~~~~

This endpoint exposes data and operations related to the group
management.
The following table summarizes supported fields. 

.. raw:: html

	<table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>ReadOnly </th>
			<th>Nullable </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>actions_on_group</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Returns the actions done on the group. The list is composed of objects, containing elements as described here.</td>
		</tr>
		<tr>
			<td><code>users</code></td>
			<td><code>related</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>Returns a list of the users belonging to the group.</td>
		</tr>
		<tr>
			<td><code>used_resources</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns the resources used by the objects the group has access to in the form of the list.</td>
		</tr>
		<tr>
			<td><code>permissions</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns the status of users permissions on different families of objects</td>
		</tr>
		<tr>
			<td><code>resource_uri</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>id</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>name</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
	</table>

**Container: actions_on_group**

This is the list of **objects**, each object consisting of
nullable fields denoted as **obj1, obj2, user, action_name**.
This container describes actions performed on the group (by
administrator, for instance) in the form of read-only information.
Please note that inclusion od **obj1** and **obj2**
depends on the action type, e.g. one of these may be omitted.

.. raw:: html

	<table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>obj1</code>, <code>obj2</code> </td>
			<td> <code>related</code> </td>
			<td> Describe action object</td>
		</tr>
		<tr>
			<td><code>timestamp</code> </td>
			<td> <code>timestamp&gt;</code> </td>
			<td> Date and time of action execution</td>
		</tr>
		<tr>
			<td><code>user</code></td>
			<td><code>related</code></td>
			<td>User performing the action</td>
		</tr>
		<tr>
			<td><code>action_name</code></td>
			<td><code>string</code></td>
			<td>Describes action name using internal descriptions</td>
		</tr>
	</table>

Example::

    <actions_on_group type="list">
    <object type="hash">
    <obj1>/api/group/1/</obj1>
    <timestamp>2011-07-29T08:28:24.566903</timestamp>
    <user>/api/user/1/</user>
    <action_name>CREATE</action_name>
    </object>
    <object type="hash">
    <obj1>/api/cluster/1/</obj1>
    <timestamp>2011-07-29T08:28:59.854791</timestamp>
    <obj2>/api/group/1/</obj2>
    <user>/api/user/1/</user>
    <action_name>ADD_USER</action_name>
    </object>
    </actions_on_group>

**Field: users**

This simple field contains a list of users belonging to the group. The
type of the resource is **related**, which means that it points
to the URI representing the resource. Example::

    <users type="list">
    <value>/api/user/2/</value>
    <value>/api/user/3/</value>
    </users>

**Container used_resources**

The syntax used here is the same as used in the <object>User</object>
resource. For more information and example, please refer to the user
section of this document.

**Container permissions**

The syntax used here is the same as used in the <object>User</object>
resource. For more information and example, please refer to the user
section of this document.


Manipulation actions
''''''''''''''''''''

.. raw:: html

	<table>
		<tr>
			<th>Action </th>
			<th>Payload </th>
			<th>Description </th>
			<th>Example </th>
		</tr>
		<tr>
			<td><code>add_user</code></td>
			<td><code>user</code></td>
			<td>Add the user to the group</td>
			<td><pre>{'action':'add_user', 'user':'/api/user/2/'}</pre></td>
		</tr>
		<tr>
			<td><code>remove_user</code></td>
			<td><code>user</code></td>
			<td>Remove the user from the group</td>
			<td><pre>{'action':'remove_user', 'user':'/api/user/2/'}</pre></td>
		</tr>
	</table>

/api/vm
~~~~~~~

This endpoint exposes methods for VirtualMachine inspection and
manipulation.

**Important**: as the attributes exposing VM object are related to many
other objects and many calls are done on different views, here the
somewhat different approach to attribute exposure is used. At the main
point **/api/vm/**, which provides a list of virtual machines,
only the basic attributes of VM are provided. However, when the
particular object is called, sad **/api/vm/3/**, the system
returns additional set of its attributes. This is due to need to perform
additional calls which introduce network latency. Performing all those
calls at once for all virtual machines could produce unnecessary
overhead.

Fields exposed (main endpoint):

.. raw:: html

	<table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>ReadOnly </th>
			<th>Nullable </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>pending_delete</code></td>
			<td><code>boolean</code></td>
			<td> </td>
			<td> </td>
			<td>Boolean data. Ex: True</td>
		</tr>
		<tr>
			<td><code>ram</code></td>
			<td><code>integer</code></td>
			<td> </td>
			<td> </td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>cluster</code></td>
			<td><code>related</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>A single related resource. Can be either a URI or set of nested resource data.</td>
		</tr>
		<tr>
			<td><code>last_job</code></td>
			<td><code>related</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>A single related resource. Can be either a URI or set of nested resource data.</td>
		</tr>
		<tr>
			<td><code>virtual_cpus</code></td>
			<td><code>integer</code></td>
			<td> </td>
			<td> </td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>id</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>hostname</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>status</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>secondary_node</code></td>
			<td><code>related</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>A single related resource. Can be either a URI or set of nested resource data.</td>
		</tr>
		<tr>
			<td><code>operating_system</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>disk_size</code></td>
			<td><code>integer</code></td>
			<td> </td>
			<td> </td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>primary_node</code></td>
			<td><code>related</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>A single related resource. Can be either a URI or set of nested resource data.</td>
		</tr>
		<tr>
			<td><code>resource_uri</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
	</table>

Fields exposed (additionally, particular object):

.. raw:: html

	<table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>ReadOnly </th>
			<th>Nullable </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>cluster_admin</code></td>
			<td><code>Boolean</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Determines if the current user has admin permissions over cluster.</td>
		</tr>
		<tr>
			<td><code>power</code></td>
			<td><code>Boolean</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Determines if the current user has admin permissions to power vm.</td>
		</tr>
		<tr>
			<td><code>modify</code></td>
			<td><code>Boolean</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Determines if the current user has admin permissions to modify vm.</td>
		</tr>
		<tr>
			<td><code>job</code></td>
			<td><code>Boolean</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Points to the jobs related to the vm, if any.</td>
		</tr>
		<tr>
			<td><code>actions_on_vm</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns the actions done on the user. The list is composed of objects, containing elements as described here.</td>
		</tr>
		<tr>
			<td><code>permissions</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Lists the objects (users and groups) having permissions over vm. Contains sublists users and groups, each having objects pointing to related user/group.</td>
		</tr>
		<tr>
			<td><code>admin</code></td>
			<td><code>Boolean</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Determines if the current user has admin permissions over vm.</td>
		</tr>
		<tr>
			<td><code>remove</code></td>
			<td><code>Boolean</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Determines if the current user has permissions to remove vm.</td>
		</tr>
		<tr>
			<td><code>migrate</code></td>
			<td><code>Boolean</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Determines if the current user has admin permissions to migrate.</td>
		</tr>
	</table>

**Containers: actions_on_vm and permissions**

The format and members of those lists are similar to previous mentioned
fields, e.g. in **cluster** endpoint. For detailed description,
please refer to those.

The field **actions_on_vm** contains object(s) taking part in
action, user initiated the action, timestamp and the internal
description of the action in form of the string. The field
**permissions>** lists users and groups (as related fields)
which have any form of permissions on virtual machine.

**Operations supported**

Operations on VM are accomplished in form of action. Action is initiated
using POST request.
Example::

    POST /api/vm/7
    {"action":"shutdown"}

In this example, user initiates @POST@ request on Virtual Machine
described with @id=7@. The action type is described in field @action@ in
request header.

After the action is initiated, server sends back response.
Example:

Header::

    HTTP/1.1 200 OK
    Date: Wed, 27 Jul 2011 18:39:31 GMT
    Server: WSGIServer/0.1 Python/2.7.1+
    Vary: Accept-Language, Cookie
    Content-Type: application/json
    Content-Language: en

Body::

    {"end_ts": null, "id": "138722", "oplog": [[]], "opresult": [null],
    "ops": [{"OP_ID": "OP_INSTANCE_SHUTDOWN", "debug_level": 0, "dry_run":
    false, "ignore_offline_nodes": false, "instance_name":
    "ooga.osuosl.org", "priority": 0, "timeout": 120}], "opstatus":
    ["running"], "received_ts": [1311791966, 837045], "start_ts":
    [1311791966, 870332], "status": "running", "summary":
    ["INSTANCE_SHUTDOWN(ooga.osuosl.org)"]}

The following actions and parameters are supported:

.. raw:: html

	<table>
		<tr>
			<td>Action</td>
			<td>Parameters</td>
			<td>Description</td>
		</tr>
		<tr>
			<td>reboot</td>
			<td></td>
			<td>Reboot VM</td>
		</tr>
		<tr>
			<td>shutdown</td>
			<td></td>
			<td>Shutdown VM</td>
		</tr>
		<tr>
			<td>startup</td>
			<td></td>
			<td>Start VM up</td>
		</tr>
		<tr>
			<td>rename</td>
			<td>hostname,ip_check,name_check</td>
			<td>Rename VM</td>
		</tr>
	</table>

/api/cluster
~~~~~~~~~~~~

This endpoint describes fields and operations available for the Cluster.

.. raw:: html

    <table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>ReadOnly </th>
			<th>Nullable </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>ram</code></td>
			<td><code>integer</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>nodes_count</code></td>
			<td><code>Integer</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns nodes count for the cluster.</td>
		</tr>
		<tr>
			<td><code>default_hypervisor</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Returns a default hypervisor for the cluster.</td>
		</tr>
		<tr>
			<td><code>virtual_cpus</code></td>
			<td><code>integer</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>disk</code></td>
			<td><code>integer</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>port</code></td>
			<td><code>integer</code></td>
			<td> </td>
			<td> </td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>hostname</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>id</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>available_ram</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns a list with elements describing RAM status, including total, allocated, used and free memory.</td>
		</tr>
		<tr>
			<td><code>master</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Returns master node</td>
		</tr>
		<tr>
			<td><code>missing_ganeti</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns a list with names of missing nodes in ganeti.</td>
		</tr>
		<tr>
			<td><code>username</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>missing_db</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns a list with names of missing nodes in DB.</td>
		</tr>
		<tr>
			<td><code>description</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>software_version</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Returns a software version.</td>
		</tr>
		<tr>
			<td><code>quota</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns a list containing objects describing quotas for the user performing the request.</td>
		</tr>
		<tr>
			<td><code>slug</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>info</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Complex container exposing many information related to the cluster. More details with example can be found in documentation/wiki.</td>
		</tr>
		<tr>
			<td><code>available_disk</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns a list with elements describing disk status, including total, allocated, used and free disk space.</td>
		</tr>
		<tr>
			<td><code>default_quota</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns a list containing objects describing default quotas.</td>
		</tr>
		<tr>
			<td><code>resource_uri</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>vm_count</code></td>
			<td><code>Integer</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Returns a number of virtual machines on the cluster.</td>
		</tr>
	</table>

**Containers: available_ram and available_disk**

The first container provides information about status of the RAM in the
cluster. Analogously, the second one provides information about disk
space in the cluster. 

.. raw:: html

    <table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>total</code> </td>
			<td> <code>Integer</code> </td>
			<td> Total RAM available to the cluster</td>
		</tr>
		<tr>
			<td><code>allocated</code> </td>
			<td> <code>Integer&gt;</code> </td>
			<td> Allocated RAM</td>
		</tr>
		<tr>
			<td><code>used</code></td>
			<td><code>Integer</code></td>
			<td>Amount of RAM used in the cluster</td>
		</tr>
		<tr>
			<td><code>free</code></td>
			<td><code>Integer</code></td>
			<td>Free RAM</td>
		</tr>
	</table>

Example::

    <available_ram type="hash">
    <allocated type="integer">1024</allocated>
    <total type="integer">2004</total>
    <used type="integer">874</used>
    <free type="integer">980</free>
    </available_ram>

**Containers: missing_ganeti and missing_db**

Here the names of the missing machines are provided in the simple form.
The former container describes machines missing in the Ganeti, while the
former contains the machines missing in the database.

Example::

    <missing_db type="list">
    <value>3429_test</value>
    <value>breakthis.gwm.osuosl.org</value>
    <value>brookjon.gwm.osuosl.org</value>
    <value>noinstall2.gwm.osuosl.org</value>
    </missing_db>

**Container: quota and default_quota**

This container returns the quotas for the user performing request. If
the user is not found or do not have a quotas assigned, default quota is
returned.
If there are no values for the specific quota element, null is returned.
Default_quota container is additionally returned for the case that quota
for the user if found.

.. raw:: html

    <table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>default</code> </td>
			<td> <code>Integer</code> </td>
			<td> Used if default quota is returned</td>
		</tr>
		<tr>
			<td><code>virtual_cpus</code> </td>
			<td> <code>Integer</code> </td>
			<td> Virtual CPUs</td>
		</tr>
		<tr>
			<td><code>ram</code></td>
			<td><code>Integer</code></td>
			<td>Amount of RAM available to the user</td>
		</tr>
		<tr>
			<td><code>disk</code></td>
			<td><code>Integer</code></td>
			<td>Amount of disk available to the user</td>
		</tr>
	</table>

Example::

    <quota type="hash">
    <default type="integer">1</default>
    <virtual_cpus type="null"/>
    <ram type="null"/>
    <disk type="null"/>
    </quota>

**Container: info**

This element provides extensive information related to the cluster.
These information are used internally in Ganeti Web Manager to render
specific pages. As of level of detail used, the field contained here
will not be described but just provided in detail in example.

::

    <info type="hash">
    <default_iallocator/>
    <maintain_node_health type="boolean">False</maintain_node_health>
    <hvparams type="hash">
    <kvm type="hash">
    <nic_type>paravirtual</nic_type>
    <use_chroot type="boolean">False</use_chroot>
    <migration_port type="integer">8102</migration_port>
    <vnc_bind_address>0.0.0.0</vnc_bind_address>
    <cdrom2_image_path/>
    <usb_mouse/>
    <migration_downtime type="integer">30</migration_downtime>
    <floppy_image_path/>
    <kernel_args>ro</kernel_args>
    <cdrom_image_path/>
    <boot_order>disk</boot_order>
    <vhost_net type="boolean">False</vhost_net>
    <disk_cache>default</disk_cache>
    <kernel_path/>
    <initrd_path/>
    <vnc_x509_verify type="boolean">False</vnc_x509_verify>
    <vnc_tls type="boolean">False</vnc_tls>
    <cdrom_disk_type/>
    <use_localtime type="boolean">False</use_localtime>
    <security_domain/>
    <serial_console type="boolean">False</serial_console>
    <kvm_flag/>
    <vnc_password_file/>
    <migration_bandwidth type="integer">32</migration_bandwidth>
    <disk_type>paravirtual</disk_type>
    <migration_mode>live</migration_mode>
    <security_model>pool</security_model>
    <root_path>/dev/vda3</root_path>
    <vnc_x509_path/>
    <acpi type="boolean">True</acpi>
    <mem_path/>
    </kvm>
    </hvparams>
    <default_hypervisor>kvm</default_hypervisor>
    <uid_pool type="list">
    <objects>
    <value type="integer">8001</value>
    <value type="integer">8030</value>
    </objects>
    </uid_pool>
    <prealloc_wipe_disks type="boolean">False</prealloc_wipe_disks>
    <primary_ip_version type="integer">4</primary_ip_version>
    <mtime type="float">1308862451.98</mtime>
    <os_hvp type="hash"/>
    <osparams type="hash"/>
    <uuid>0b3b2432-a8e1-4c17-a99b-87303841cb95</uuid>
    <export_version type="integer">0</export_version>
    <hidden_os type="list"/>
    <master>gwm1.osuosl.org</master>
    <nicparams type="hash">
    <default type="hash">
    <link>br0</link>
    <mode>bridged</mode>
    </default>
    </nicparams>
    <protocol_version type="integer">2040000</protocol_version>
    <config_version type="integer">2040000</config_version>
    <software_version>2.4.2</software_version>
    <tags type="list"/>
    <os_api_version type="integer">20</os_api_version>
    <candidate_pool_size type="integer">10</candidate_pool_size>
    <file_storage_dir>/var/lib/ganeti-storage/file</file_storage_dir>
    <blacklisted_os type="list"/>
    <enabled_hypervisors type="list">
    <value>kvm</value>
    </enabled_hypervisors>
    <drbd_usermode_helper>/bin/true</drbd_usermode_helper>
    <reserved_lvs type="list"/>
    <ctime type="float">1292887189.41</ctime>
    <name>gwm.osuosl.org</name>
    <master_netdev>eth0</master_netdev>
    <ndparams type="hash">
    <oob_program type="null"/>
    </ndparams>
    <architecture type="list">
    <value>64bit</value>
    <value>x86_64</value>
    </architecture>
    <volume_group_name>ganeti</volume_group_name>
    <beparams type="hash">
    <default type="hash">
    <auto_balance type="boolean">True</auto_balance>
    <vcpus type="integer">2</vcpus>
    <memory type="integer">512</memory>
    </default>
    </beparams>
    </info>

/api/node
~~~~~~~~~

In this endpoint exposed are the attributes and operations on the
Cluster.

.. raw:: html

    <table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>ReadOnly </th>
			<th>Nullable </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>info</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>This complex field returns various information related to the node.</td>
		</tr>
		<tr>
			<td><code>ram_free</code></td>
			<td><code>integer</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>Admin</code></td>
			<td><code>boolean</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Determines if the user has admin status on the node</td>
		</tr>
		<tr>
			<td><code>hostname</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Hostname of the node</td>
		</tr>
		<tr>
			<td><code>modify</code></td>
			<td><code>boolean</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Determines if the user is able to modify node parameters</td>
		</tr>
		<tr>
			<td><code>cluster</code></td>
			<td><code>related</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Cluster the node belongs to</td>
		</tr>
		<tr>
			<td><code>disk_total</code></td>
			<td><code>integer</code></td>
			<td> </td>
			<td> </td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>node_count</code></td>
			<td><code>Integer</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Number of the nodes in the cluster</td>
		</tr>
		<tr>
			<td><code>last_job</code></td>
			<td><code>related</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>A single related resource. Can be either a URI or set of nested resource data.</td>
		</tr>
		<tr>
			<td><code>disk_free</code></td>
			<td><code>integer</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>ram_total</code></td>
			<td><code>integer</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>role</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>offline</code></td>
			<td><code>boolean</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Boolean data. Ex: True</td>
		</tr>
		<tr>
			<td><code>id</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>primary_list</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x </td>
			<td>List of virtual machines (primary node). Contains vm link (related) and hostname for particular object.</td>
		</tr>
		<tr>
			<td><code>secondary_list</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x </td>
			<td>List of virtual machines (secondary node). Contains vm link (related) and hostname for particular object.</td>
		</tr>
		<tr>
			<td><code>actions_on_node</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Returns the actions done on the node. The list is composed of objects, containing elements as described here.</td>
		</tr>
		<tr>
			<td><code>resource_uri</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
	</table>

**Container: actions_on_node**

This container provides the actions done on the node in form of the log.
It is similar in the form to the other actions_on_X containers in other
endpoints. For more info please take a look there.

**Container: primary_list and secondary_list**

These containers provide the list of virtual machines existing on the
node in primary and secondary node mode.
The list is simple and includes object hostname and related link.
Example::

    <primary_list type="list">
    <object type="hash">
    <hostname>3429</hostname>
    <resource>/api/vm/1/</resource>
    </object>
    <object type="hash">
    <hostname>breakthis.gwm.osuosl.org</hostname>
    <resource>/api/vm/2/</resource>
    </object>
    </primary_list>

**Container: info**

This element provides extensive information related to the node. These
information are used internally in Ganeti Web Manager to render specific
pages. As of level of detail used, the field contained here will be
described partially only. It should be noted that the elements in the
table may be nullable. The full example output is included after the
table.

.. raw:: html

    <table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>pinst_cnt</code> </td>
			<td> <code>Integer</code> </td>
			<td> Number of virtual machines for which the node is primary</td>
		</tr>
		<tr>
			<td><code>sinst_cnt</code> </td>
			<td> <code>Integer</code> </td>
			<td> Number of virtual machines for which the node is secondary</td>
		</tr>
		<tr>
			<td><code>pinst_list</code> </td>
			<td> <code>List</code> </td>
			<td> Virtual machines on this node (primary)</td>
		</tr>
		<tr>
			<td><code>sinst_list</code> </td>
			<td> <code>List</code> </td>
			<td> Virtual machines on this node (secondary)</td>
		</tr>
		<tr>
			<td><code>drained</code> </td>
			<td> <code>Boolean</code> </td>
			<td> Determines if the node is drained</td>
		</tr>
		<tr>
			<td><code>offline</code> </td>
			<td> <code>Boolean</code> </td>
			<td> Determines if the node is ofline</td>
		</tr>
		<tr>
			<td><code>vm_capable</code> </td>
			<td> <code>Boolean</code> </td>
			<td> Determines if the node is capable of hosting virtual machines</td>
		</tr>
		<tr>
			<td><code>master_capable</code> </td>
			<td> <code>Boolean</code> </td>
			<td> Determines if the node is capable to become master node</td>
		</tr>
		<tr>
			<td><code>master_candidate</code> </td>
			<td> <code>Boolean</code> </td>
			<td> Determines if the node is master candidate</td>
		</tr>
		<tr>
			<td><code>mnode</code> </td>
			<td> <code>Boolean</code> </td>
			<td> Determines if the node is active master node</td>
		</tr>
		<tr>
			<td><code>pip</code> </td>
			<td> <code>String</code> </td>
			<td> Primary IP address of the node</td>
		</tr>
		<tr>
			<td><code>sip</code> </td>
			<td> <code>String</code> </td>
			<td> Secondary IP address of the node</td>
		</tr>
		<tr>
			<td><code>uuid</code> </td>
			<td> <code>String</code> </td>
			<td> UUID</td>
		</tr>
		<tr>
			<td><code>group.uuid</code> </td>
			<td> <code>String</code> </td>
			<td>group UUID</td>
		</tr>
		<tr>
			<td><code>tags</code> </td>
			<td> <code>List</code> </td>
			<td> Tags attached to the node</td>
		</tr>
	</table>

::

    <info type="hash">
    <dfree type="integer">30336</dfree>
    <cnodes type="integer">1</cnodes>
    <serial_no type="integer">1</serial_no>
    <dtotal type="integer">60012</dtotal>
    <sinst_cnt type="integer">0</sinst_cnt>
    <mtime type="null"/>
    <pip>140.211.15.61</pip>
    <mfree type="integer">1310</mfree>
    <sip>140.211.15.61</sip>
    <uuid>4a0e9df5-0b59-4643-b156-c133edb035bc</uuid>
    <drained type="boolean">False</drained>
    <sinst_list type="list"/>
    <csockets type="integer">1</csockets>
    <role>M</role>
    <ctotal type="integer">2</ctotal>
    <offline type="boolean">False</offline>
    <vm_capable type="boolean">True</vm_capable>
    <pinst_cnt type="integer">15</pinst_cnt>
    <mtotal type="integer">2004</mtotal>
    <tags type="list"/>
    <group.uuid>e318906a-40cd-4702-813b-c2185abaf8ec</group.uuid>
    <master_capable type="boolean">True</master_capable>
    <ctime type="null"/>
    <master_candidate type="boolean">True</master_candidate>
    <name>gwm1.osuosl.org</name>
    <mnode type="integer">730</mnode>
    <pinst_list type="list">
    <value>3429</value>
    <value>noinstall2.gwm.osuosl.org</value>
    <value>failed</value>
    <value>success</value>
    <value>derpers.gwm.osuosl.org</value>
    <value>testtest</value
    ><value>breakthis.gwm.osuosl.org</value>
    <value>foobarherpderp.gwm</value>
    <value>brookjon.gwm.osuosl.org</value>
    <value>orphanme</value>
    <value>foobar352</value>
    <value>testcdrom2.gwm.osuosl.org</value>
    <value>ooga.osuosl.org</value>
    <value>diskless3</value>
    <value>noinstall.gwm.osuosl.org</value>
    </pinst_list>
    </info>

/api/job
~~~~~~~~

This endpoint exposes information related to the job execution in the
system.

.. raw:: html

	<table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>ReadOnly </th>
			<th>Nullable </th>
			<th>Description </th>
		</tr>
		<tr>
			<td><code>status</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
		<tr>
			<td><code>summarys</code></td>
			<td><code>string</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Describes the job summary.</td>
		</tr>
		<tr>
			<td><code>job_id</code></td>
			<td><code>integer</code></td>
			<td> </td>
			<td> </td>
			<td>Integer data. Ex: 2673</td>
		</tr>
		<tr>
			<td><code>cluster_admin</code></td>
			<td><code>Boolean</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Determines if the current user has admin permissions over related cluster.</td>
		</tr>
		<tr>
			<td><code>ops</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td> </td>
			<td>Complex field containing details about job. The field contents depend on the job type. More details can be found in the wiki.</td>
		</tr>
		<tr>
			<td><code>opresult</code></td>
			<td><code>list</code></td>
			<td style="text-align:center;">x</td>
			<td style="text-align:center;">x</td>
			<td>Describes the error occurred during job execution.</td>
		</tr>
		<tr>
			<td><code>cluster</code></td>
			<td><code>related</code></td>
			<td> </td>
			<td> </td>
			<td>A single related resource. Can be either a URI or set of nested resource data.</td>
		</tr>
		<tr>
			<td><code>finished</code></td>
			<td><code>datetime</code></td>
			<td> </td>
			<td style="text-align:center;">x</td>
			<td>A date &#38; time as a string. Ex: "2010-11-10T03:07:43"</td>
		</tr>
		<tr>
			<td><code>cleared</code></td>
			<td><code>boolean</code></td>
			<td> </td>
			<td> </td>
			<td>Boolean data. Ex: True</td>
		</tr>
		<tr>
			<td><code>resource_uri</code></td>
			<td><code>string</code></td>
			<td> </td>
			<td> </td>
			<td>Unicode string data. Ex: "Hello World"</td>
		</tr>
	</table>

**Container: opresult**

This field contains a detailed description of error encountered during
job execution.
The fields included are the following:

.. raw:: html

	<table>
		<tr>
			<th>Name </th>
			<th>Type </th>
			<th>Description </th>
		</tr>
		<tr>
			<td>error_type</td>
			<td>string</td>
			<td>Denotes the type of the error</td>
		</tr>
		<tr>
			<td>error_message</td>
			<td>string</td>
			<td>Contains a summary description of the error. May be omitted.</td>
		</tr>
		<tr>
			<td>error_family</td>
			<td>string</td>
			<td>Relates error to the family of errors. May be omitted.</td>
		</tr>
	</table>

Example::

    <opresult type="hash">
    <error_type>OpPrereqError</error_type>
    <error_message>The given name (owelwjqe) does not resolve: Name or
    service not known</error_message>
    <error_family>resolver_error</error_family>
    </opresult>

**Container: ops**
This field contains information about the job executed. There may be
many subfields included, spanned through several levels.

The following excerpts provide two typical example outputs:

::

    <pre>
    <ops type="list">
    <object type="hash">
    <hvparams type="hash">
    <nic_type>paravirtual</nic_type>
    <boot_order>disk</boot_order>
    <root_path>/dev/vda3</root_path>
    <serial_console type="boolean">False</serial_console>
    <cdrom_image_path/>
    <disk_type>paravirtual</disk_type>
    <kernel_path/>
    </hvparams>
    <debug_level type="integer">0</debug_level>
    <disk_template>plain</disk_template>
    <name_check type="boolean">True</name_check>
    <osparams type="hash"/>
    <src_node type="null"/>
    <source_x509_ca type="null"/>
    <dry_run type="boolean">False</dry_run>
    <pnode>gwm1.osuosl.org</pnode>
    <nics type="list">
    <object type="hash">
    <link>br0</link>
    <mode>bridged</mode>
    </object>
    </nics>
    <wait_for_sync type="boolean">True</wait_for_sync>
    <priority type="integer">0</priority>
    <start type="boolean">True</start>
    <ip_check type="boolean">True</ip_check>
    <source_shutdown_timeout type="integer">120</source_shutdown_timeout>
    <file_storage_dir type="null"/>
    <no_install type="boolean">False</no_install>
    <src_path type="null"/>
    <snode type="null"/>
    <identify_defaults type="boolean">False</identify_defaults>
    <OP_ID>OP_INSTANCE_CREATE</OP_ID>
    <source_instance_name type="null"/>
    <source_handshake type="null"/>
    <hypervisor>kvm</hypervisor>
    <force_variant type="boolean">False</force_variant>
    <disks type="list">
    <object type="hash">
    <size type="integer">408</size>
    </object>
    </disks>
    <instance_name>owelwjqe</instance_name>
    <mode>create</mode>
    <iallocator type="null"/>
    <file_driver>loop</file_driver>
    <os_type>image+debian-squeeze</os_type>
    <beparams type="hash">
    <vcpus type="integer">2</vcpus>
    <memory type="integer">512</memory>
    </beparams>
    </object>
    </ops>
    </pre>

::

    <pre>
    <ops type="list">
    <object type="hash">
    <instance_name>brookjon.gwm.osuosl.org</instance_name>
    <ignore_secondaries type="boolean">False</ignore_secondaries>
    <dry_run type="boolean">False</dry_run>
    <priority type="integer">0</priority>
    <debug_level type="integer">0</debug_level>
    <OP_ID>OP_INSTANCE_REBOOT</OP_ID>
    <reboot_type>hard</reboot_type>
    <shutdown_timeout type="integer">120</shutdown_timeout>
    </object>
    </ops>
    </pre>
