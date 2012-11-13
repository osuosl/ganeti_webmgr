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
using the GWM mailing list at
http://groups.google.com/group/ganeti-webmgr or issue tracker located at
http://code.osuosl.org/projects/ganeti-webmgr/issues.
Please put the line [REST-API] in the subject if you are sending email
message.

REST API for GWM can now be considered as a beta software. For the
further development the following is proposed:

*Roadmap:*
* completion of unit tests
* relocate parts of endpoints which may contain long answers - that
variables should be accessed separately (such as object logs)
* further refinement of the code and documentation
* work on further integration (like cloud driver)

The *users/developers/visitors are advised to test* the code and *submit
the comments/notices/wishes*. Comments can be submitted either directly
to the author, here on this wiki or using the Redmine ticket at
[[https://code.osuosl.orghttp://code.osuosl.org/issues/3573]].

The version containing significant changes to this version may be
expected in *November 2011*.

About this documentation
------------------------

This documentation covers basic functionality of the REST API. It
consists of the subsections, referring to particular endpoints forming
the API. As an endpoints referred are application resources exposed as
URIs through appropriate hierarchy. Currently, the system exposes the
following resources as REST API endpoints: <code>User</code>,
<code>Group</code>, <code>Virtual Machine</code>, <code>Cluster</code>,
<code>Node</code>, <code>Job</code>. These are accessible in the form of
CRUD operations using HTTP protocol.

By default, each API endpoint returns a list of resources.

For example:
<pre>
/api/vm/
</pre> would return a list of Virtual Machines in the system, while the
particular VM resource is accessed through: <pre>
/api/vm/1/
</pre>
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

While <code>type</code> field represents basic data types, it should be
noted that <code>related</code> type points to other resource in the
system.
For example:
<pre>
...
<cluster>
...
<virtualmachine>
/api/vm/5
</virtualmachine>
</cluster>
...
</pre> says that particular cluster resource includes virtualmachine
resource, described by related URI. Therefore, if necessary, the
complete resource referred at that point may be obtained through
provided URI.

This documentation trends to provide as much as complete list of
resources and their schematic description. However, due to the level of
deepness and limitations of the current wiki system, in some cases this
representation is simplified and explained in words rather than in
tabular form. It should be noted that all these descriptions are already
included in the system.
Using
<pre>
http://somesite.com/api/?format=xml
</pre> user is able to get the list of resources exposed, while with the
help of
<pre>
http://somesite.com/api/resource/schema/?format=xml
</pre>
the system returns detailed schema of resource representation and field
properties in XML format. Therefore, the user is always able to take a
look and check detailed description about a resource, if the one
provided here in documentation is not detailed and clear enough.

h1. Design principles

This API aims to expose the resources of Ganeti Web Manager, making
suitable for integration into other systems or just performing of simple
operations on resources. It does not aim to expose all resources and
functions contained in the software, but only the set deemed necessary
in order to support its business functions. Currently, it means that the
most of the functionality present in the web interface is available for
usage and manipulation also using this REST API.

h1. Installation

The most of the code of this addon comes under <code>/api</code>
directory of GWM distribution. Other code changes are done in some of
views and dependent modules (like <code>django_object_log</code> and
<code>django_object_permissions</code>). Its inclusion in the GWM is
done in <code>/urls.py</code> via:

<pre>
urlpatterns = patterns('',
...
    (r'^', include('api.urls')),
...
</pre>

The prerequisite for running RESTful API over Ganeti Web Manager is to
have <code>django-tastypie</code> installed. The latest active
version/commit of <code>tastypie</code> should be used in order to
support <code>ApiKeys</code> based authentication. That means, as of
time of writing this documentation, that <code>tastypie</code> should be
installed manually. Additionally, the following line in
<code>tastypie/authentication.py</code>:
<pre>
username = request.GET.get('username') or request.POST.get('username')
</pre>

should be changed to:

<pre>
username = request.GET.get('username') or request.POST.get('username')
or request.GET.get('user') or request.POST.get('user')
</pre>

This is the known issue with <code>tastypie</code> already reported in
its bug system. If not changed, the part <code>username</code> in
<code>/api/user/?api_key=xxx&username=xxx</code> will produce error
message during browsing the main user endpoint. This change makes
<code>tastypie</code> to accept <code>user</code> for authentication
instead of <code>username</code>. Later produces collision with the
field of the same name under <code>User</code> model class.

The next change related to the installation of the module is inclusion
of <code>'tastypie'</code> in <code>INSTALLED_APPS</code> of
<code>settings.py</code>. This will produce necessary tables during
installation/migration.

h2. Development

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

The framework used to introduce RESTful interface is *django-tastypie*.
It has been selected after initial research and testing of several
popular Python/Django/REST frameworks. The system supports both XML and
JSON as input/output serializations.

h2. Authentication and Authorization

The authentication is done using <code>API keys</code>. For each user
the appropriate API key is generated automatically. The key can be
renewed/recreated using <code>POST</code> request and appropriate action
inside API. The access to the system looks like in the following
example:
<pre>
http://localhost:8000/api/?format=xml&api_key=381a5987a611fb1f8c68ffad49d2cd2b9f92db71&user=test
</pre>

Please note that <code>username</code> initially supported by
<code>tastypie</code> has been replaced with <code>user</code> in the
example query above. The changes and reasons are described in the
installation section of this document.

Authorization is completely dependent on Django's authorization system.
The existing views from the GWM have been used to expose the most of
resources available. Those views are already integrated in Django's
authorization system. Therefore, this API should not contain critical
security flaws or problems and should be easier to maintenance.

h1. REST API endpoints

h2. /api/user

This endpoint exposes data and operations related to the user
management.
The following table provides the descriptions of the fields:

|_. Name |_. Type |_. ReadOnly |_. Nullable |_. Description |_.
|<code>username</code>|<code>string</code>| | |Required. 30 characters
or fewer. Letters, numbers and @/./+/-/_ characters|
|<code>ssh_keys</code>|<code>list</code>| |=. x|SSH keys for user's
account. The list may be composed of several objects.|
|<code>first_name</code>|<code>string</code>| | |Unicode string data.
Ex: "Hello World"|
|<code>last_name</code>|<code>string</code>| | |Unicode string data. Ex:
"Hello World"|
|<code>actions_on_user</code>|<code>list</code>|=. x|=. x|Returns the
actions done on the user. The list is composed of objects, containing
elements as described here.|
|<code>groups</code>|<code>related</code>|=. x|=. x|Returns the groups
the user is member of|
|<code>api_key</code>|<code>string</code>|=. x|=. x|Returns the api key
of the user|
|<code>used_resources</code>|<code>list</code>|=. x|=. x|Returns the
resources used by the objects user has access to in the form of the
list.|
|<code>is_active</code>|<code>boolean</code>| | |Designates whether this
user should be treated as active. Unselect this instead of deleting
accounts.|
|<code>id</code>|<code>string</code>|=. x| |Unicode string data. Ex:
"Hello World"|
|<code>is_superuser</code>|<code>boolean</code>| | |Designates that this
user has all permissions without explicitly assigning them.|
|<code>is_staff</code>|<code>boolean</code>| | |Designates whether the
user can log into this admin site.|
|<code>last_login</code>|<code>datetime</code>| | |A date & time as a
string. Ex: "2010-11-10T03:07:43"|
|<code>date_joined</code>|<code>datetime</code>| | |A date & time as a
string. Ex: "2010-11-10T03:07:43"|
|<code>user_actions</code>|<code>list</code>|=. x| |Returns the actions
done by the user. The list is composed of objects, containing elements
as described here.|
|<code>permissions</code>|<code>list</code>|=. x|=. x|Returns the status
of users permissions on different families of objects|
|<code>password</code>|<code>string</code>| | |Returns hashed password|
|<code>email</code>|<code>string</code>| | |Unicode string data. Ex:
"Hello World"|
|<code>resource_uri</code>|<code>string</code>|=. x| |Unicode string
data. Ex: "Hello World"|

h3. Explanations for particular list elements 

*Container: ssh_keys*

The elements of the list are denoted as <code>value</code> nodes,
containing paricular ssh key for the user in the form of <code>string
hash</code>

Example:

<pre>
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
</pre>

*Containers: user_actions and actions_on_users*

This is the list of <code>objects</code>, each object consisting of
nullable fields denoted as <code>obj1, obj2, user, action_name</code>.
The both containers share the representation. The difference between
these is the fact that first describes actions performed by user, while
the second one describes actions performed on user (by administrator,
for instance).
The both containers provide read only information.

|_. Name |_. Type |_. Description |
|<code>obj1</code>, <code>obj2</code> | <code>related</code> | Describe
action object|
|<code>timestamp</code> | <code>timestamp></code> | Date and time of
action execution|
|<code>user</code>|<code>related</code>|User performing the action|
|<code>action_name</code>|<code>string</code>|Describes action name
using internal descriptions|

Example:

<pre>
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
</pre>

*Container used_resources*

This list consists of <code>object</code> elements, each containing
<code>resource</code>, <code>object</code> and <code>type</code>.
The field <code>object</code> represents related resource for which the
system resources consumption is given. The <code>type</code> is
<code>string</code> describing the object type using internal
descriptions (like <code>VirtualMachine</code> for virtual machine).
The <code>resource</code> contains subfields <code>virtual_cpus</code>,
<code>disk</code> and <code>ram</code>, each of type
<code>integer</code> and representing actual consumption of the
particular system resource in system's default dimension (e.g. MBs for
RAM consumption).

Example:
<pre>
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
</pre>

*Container permissions*

<code>Permissions</code> contains elements describing particular
resource type, each further containing a list of resources. The primary
<code>elements</code> are described as <code>Cluster</code>,
<code>VirtualMachine</code>, <code>Group</code>. Their list member main
nodes are described as <code>object</code>, containing
<code>object</code> reference (related resource) for which the
permissions are set, and the <code>permissions</code> list containing
list of <code>values</code> as strings, describing permission type in
internal format (like <code>create_vm</code>).

Example:

<pre>
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
</pre>


h3. Manipulation and operations using POST/PUT/DELETE methods

The fields marked as non-readonly (table above) can be subject of
further manipulation and operations. *The same applies to the rest of
the document - those fields can be automatically updated or deleted by
performing analog request.*
In order to maintain consistency with REST approach, the
<code>PUT</code> method is used on currently available resources with
purpose to change or update them. On another side, <code>POST</code>
method is used either to generate new resources, or to perform
predefined actions on currently existing resources.

The following example demonstrates changing of users lastname and status
in system (disabling its account).
Request URI:
<pre>
PUT /api/user/1/?api_key=xxxxx&username=yyyyy
</pre>
Request header:
<pre>
Content-Type: application/json
Accept: application/json
</pre>
Request payload:
<pre>
{"last_name":"New LastName", "is_active":false}
</pre>

Server response:
<pre>
HTTP/1.1 204 NO CONTENT
Date: Sat, 06 Aug 2011 11:18:25 GMT
Server: WSGIServer/0.1 Python/2.7.1+
Vary: Accept-Language, Cookie
Content-Length: 0
Content-Type: text/html; charset=utf-8
Content-Language: en
</pre>

The next example demonstrates generating of new Api key for the user:

Request URI:
<pre>
POST /api/user/2/?api_key=xxxxx&username=yyyyy
</pre>
Request header:
<pre>
Content-Type: application/json
Accept: application/xml
</pre>
Request payload:
<pre>
{"action":"generate_api_key"}
</pre>

Server response:
<pre>
HTTP/1.1 201 CREATED
Date: Sat, 06 Aug 2011 11:21:56 GMT
Server: WSGIServer/0.1 Python/2.7.1+
Vary: Accept-Language, Cookie
Content-Type: text/html; charset=utf-8
Content-Language: en
</pre>

Response body:
<pre>
<?xml version='1.0' encoding='utf-8'?>
<object>
<api_key>de0a57db0ce43d0f3c52f83eaf33387750ac9953</api_key>
<userid>2</userid>
</object>
</pre>


For the API Key manipulation under <code>/api/user/</code> endpoint
implemented are two POST actions: <code>generate_api_key</code>, as
demonstrated in the example above, and <code>clean_api_key</code>.
The former generates a new API key for the user and returns it in the
response, while the later one cleans user's API key. This way its access
to the system using REST API is disabled, but the standard access using
web interface is untouch.

Additionally, two POST actions are implemented for user-group membership
manipulation.

|_. Action |_. Payload |_. Description |_. Example |
|<code>add_to_group</code>|<code>group</code>|Add the user to the
group|<pre>{'action':'add_to_group', 'group':'/api/group/1/'}</pre>|
|<code>remove_from_group</code>|<code>group</code>|Remove the user from
the group|<pre>{'action':'remove_from_group',
'group':'/api/group/1/'}</pre>|
|<code>generate_api_key</code>|=. -|Generate API key for the user
|<pre>{'action':'generate_api_key'}</pre>|
|<code>clean_api_key</code>|=. -|Clean API key for the user
|<pre>{'action':'clean_api_key'}</pre>|

h2. /api/group

This endpoint exposes data and operations related to the group
management.
The following table summarizes supported fields. 

|_. Name |_. Type |_. ReadOnly |_. Nullable |_. Description |_.
|<code>actions_on_group</code>|<code>list</code>|=. x| |Returns the
actions done on the group. The list is composed of objects, containing
elements as described here.|
|<code>users</code>|<code>related</code>| |=. x|Returns a list of the
users belonging to the group.|
|<code>used_resources</code>|<code>list</code>|=. x|=. x|Returns the
resources used by the objects the group has access to in the form of the
list.|
|<code>permissions</code>|<code>list</code>|=. x|=. x|Returns the status
of users permissions on different families of objects|
|<code>resource_uri</code>|<code>string</code>|=. x| |Unicode string
data. Ex: "Hello World"|
|<code>id</code>|<code>string</code>|=. x| |Unicode string data. Ex:
"Hello World"|
|<code>name</code>|<code>string</code>| | |Unicode string data. Ex:
"Hello World"|

*Container: actions_on_group*

This is the list of <code>objects</code>, each object consisting of
nullable fields denoted as <code>obj1, obj2, user, action_name</code>.
This container describes actions performed on the group (by
administrator, for instance) in the form of read-only information.
Please note that inclusion od <code>obj1</code> and <code>obj2</code>
depends on the action type, e.g. one of these may be omitted.

|_. Name |_. Type |_. Description |
|<code>obj1</code>, <code>obj2</code> | <code>related</code> | Describe
action object|
|<code>timestamp</code> | <code>timestamp></code> | Date and time of
action execution|
|<code>user</code>|<code>related</code>|User performing the action|
|<code>action_name</code>|<code>string</code>|Describes action name
using internal descriptions|

Example:

<pre>
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
</pre>


*Field: users*

This simple field contains a list of users belonging to the group. The
type of the resource is <code>related</code>, which means that it points
to the URI representing the resource. Example:

<pre>
<users type="list">
<value>/api/user/2/</value>
<value>/api/user/3/</value>
</users>
</pre>


*Container used_resources*

The syntax used here is the same as used in the <object>User</object>
resource. For more information and example, please refer to the user
section of this document.

*Container permissions*

The syntax used here is the same as used in the <object>User</object>
resource. For more information and example, please refer to the user
section of this document.



h3. Manipulation actions

|_. Action |_. Payload |_. Description |_. Example |
|<code>add_user</code>|<code>user</code>|Add the user to the
group|<pre>{'action':'add_user', 'user':'/api/user/2/'}</pre>|
|<code>remove_user</code>|<code>user</code>|Remove the user from the
group|<pre>{'action':'remove_user', 'user':'/api/user/2/'}</pre>|



h2. /api/vm

This endpoint exposes methods for VirtualMachine inspection and
manipulation.

*Important*: as the attributes exposing VM object are related to many
other objects and many calls are done on different views, here the
somewhat different approach to attribute exposure is used. At the main
point <code>/api/vm/</code>, which provides a list of virtual machines,
only the basic attributes of VM are provided. However, when the
particular object is called, sad <code>/api/vm/3/</code>, the system
returns additional set of its attributes. This is due to need to perform
additional calls which introduce network latency. Performing all those
calls at once for all virtual machines could produce unnecessary
overhead.

Fields exposed (main endpoint):

|_. Name |_. Type |_. ReadOnly |_. Nullable |_. Description |_.
|<code>pending_delete</code>|<code>boolean</code>| | |Boolean data. Ex:
True|
|<code>ram</code>|<code>integer</code>| | |Integer data. Ex: 2673|
|<code>cluster</code>|<code>related</code>| |=. x|A single related
resource. Can be either a URI or set of nested resource data.|
|<code>last_job</code>|<code>related</code>| |=. x|A single related
resource. Can be either a URI or set of nested resource data.|
|<code>virtual_cpus</code>|<code>integer</code>| | |Integer data. Ex:
2673|
|<code>id</code>|<code>string</code>| | |Unicode string data. Ex: "Hello
World"|
|<code>hostname</code>|<code>string</code>| | |Unicode string data. Ex:
"Hello World"|
|<code>status</code>|<code>string</code>| | |Unicode string data. Ex:
"Hello World"|
|<code>secondary_node</code>|<code>related</code>| |=. x|A single
related resource. Can be either a URI or set of nested resource data.|
|<code>operating_system</code>|<code>string</code>| | |Unicode string
data. Ex: "Hello World"|
|<code>disk_size</code>|<code>integer</code>| | |Integer data. Ex: 2673|
|<code>primary_node</code>|<code>related</code>| |=. x|A single related
resource. Can be either a URI or set of nested resource data.|
|<code>resource_uri</code>|<code>string</code>| | |Unicode string data.
Ex: "Hello World"|

Fields exposed (additionally, particular object):

|_. Name |_. Type |_. ReadOnly |_. Nullable |_. Description |_.
|<code>cluster_admin</code>|<code>Boolean</code>|=. x| |Determines if
the current user has admin permissions over cluster.|
|<code>power</code>|<code>Boolean</code>|=. x| |Determines if the
current user has admin permissions to power vm.|
|<code>modify</code>|<code>Boolean</code>|=. x| |Determines if the
current user has admin permissions to modify vm.|
|<code>job</code>|<code>Boolean</code>|=. x|=. x|Points to the jobs
related to the vm, if any.|
|<code>actions_on_vm</code>|<code>list</code>|=. x|=. x|Returns the
actions done on the user. The list is composed of objects, containing
elements as described here.|
|<code>permissions</code>|<code>list</code>|=. x| |Lists the objects
(users and groups) having permissions over vm. Contains sublists users
and groups, each having objects pointing to related user/group.|
|<code>admin</code>|<code>Boolean</code>|=. x| |Determines if the
current user has admin permissions over vm.|
|<code>remove</code>|<code>Boolean</code>|=. x| |Determines if the
current user has permissions to remove vm.|
|<code>migrate</code>|<code>Boolean</code>|=. x| |Determines if the
current user has admin permissions to migrate.|


*Containers: actions_on_vm and permissions*

The format and members of those lists are similar to previous mentioned
fields, e.g. in <code>cluster</code> endpoint. For detailed description,
please refer to those.

The field <code>actions_on_vm</code> contains object(s) taking part in
action, user initiated the action, timestamp and the internal
description of the action in form of the string. The field
<code>permissions></code> lists users and groups (as related fields)
which have any form of permissions on virtual machine.

*Operations supported*

Operations on VM are accomplished in form of action. Action is initiated
using POST request.
Example: 
<pre>
POST /api/vm/7
{"action":"shutdown"}
</pre>
In this example, user initiates @POST@ request on Virtual Machine
described with @id=7@. The action type is described in field @action@ in
request header.

After the action is initiated, server sends back response.
Example:

Header:
<pre>
HTTP/1.1 200 OK
Date: Wed, 27 Jul 2011 18:39:31 GMT
Server: WSGIServer/0.1 Python/2.7.1+
Vary: Accept-Language, Cookie
Content-Type: application/json
Content-Language: en
</pre>
Body:
<pre>
{"end_ts": null, "id": "138722", "oplog": [[]], "opresult": [null],
"ops": [{"OP_ID": "OP_INSTANCE_SHUTDOWN", "debug_level": 0, "dry_run":
false, "ignore_offline_nodes": false, "instance_name":
"ooga.osuosl.org", "priority": 0, "timeout": 120}], "opstatus":
["running"], "received_ts": [1311791966, 837045], "start_ts":
[1311791966, 870332], "status": "running", "summary":
["INSTANCE_SHUTDOWN(ooga.osuosl.org)"]}
</pre>

The following actions and parameters are supported:

|Action|Parameters|Description|
|reboot||Reboot VM|
|shutdown||Shutdown VM|
|startup||Start VM up|
|rename|hostname,ip_check,name_check|Rename VM|


h2. /api/cluster

This endpoint describes fields and operations available for the Cluster.

|_. Name |_. Type |_. ReadOnly |_. Nullable |_. Description |_.
|<code>ram</code>|<code>integer</code>| |=. x|Integer data. Ex: 2673|
|<code>nodes_count</code>|<code>Integer</code>|=. x|=. x|Returns nodes
count for the cluster.|
|<code>default_hypervisor</code>|<code>string</code>|=. x| |Returns a
default hypervisor for the cluster.|
|<code>virtual_cpus</code>|<code>integer</code>| |=. x|Integer data. Ex:
2673|
|<code>disk</code>|<code>integer</code>| |=. x|Integer data. Ex: 2673|
|<code>port</code>|<code>integer</code>| | |Integer data. Ex: 2673|
|<code>hostname</code>|<code>string</code>| | |Unicode string data. Ex:
"Hello World"|
|<code>id</code>|<code>string</code>| | |Unicode string data. Ex: "Hello
World"|
|<code>available_ram</code>|<code>list</code>|=. x|=. x|Returns a list
with elements describing RAM status, including total, allocated, used
and free memory.|
|<code>master</code>|<code>string</code>|=. x| |Returns master node|
|<code>missing_ganeti</code>|<code>list</code>|=. x|=. x|Returns a list
with names of missing nodes in ganeti.|
|<code>username</code>|<code>string</code>| |=. x|Unicode string data.
Ex: "Hello World"|
|<code>missing_db</code>|<code>list</code>|=. x|=. x|Returns a list with
names of missing nodes in DB.|
|<code>description</code>|<code>string</code>| |=. x|Unicode string
data. Ex: "Hello World"|
|<code>software_version</code>|<code>string</code>|=. x| |Returns a
software version.|
|<code>quota</code>|<code>list</code>|=. x|=. x|Returns a list
containing objects describing quotas for the user performing the
request.|
|<code>slug</code>|<code>string</code>| | |Unicode string data. Ex:
"Hello World"|
|<code>info</code>|<code>list</code>|=. x|=. x|Complex container
exposing many information related to the cluster. More details with
example can be found in documentation/wiki.|
|<code>available_disk</code>|<code>list</code>|=. x|=. x|Returns a list
with elements describing disk status, including total, allocated, used
and free disk space.|
|<code>default_quota</code>|<code>list</code>|=. x|=. x|Returns a list
containing objects describing default quotas.|
|<code>resource_uri</code>|<code>string</code>| | |Unicode string data.
Ex: "Hello World"|
|<code>vm_count</code>|<code>Integer</code>|=. x|=. x|Returns a number
of virtual machines on the cluster.|


*Containers: available_ram and available_disk*

The first container provides information about status of the RAM in the
cluster. Analogously, the second one provides information about disk
space in the cluster. 

|_. Name |_. Type |_. Description |
|<code>total</code> | <code>Integer</code> | Total RAM available to the
cluster|
|<code>allocated</code> | <code>Integer></code> | Allocated RAM|
|<code>used</code>|<code>Integer</code>|Amount of RAM used in the
cluster|
|<code>free</code>|<code>Integer</code>|Free RAM|

Example:
<pre>
<available_ram type="hash">
<allocated type="integer">1024</allocated>
<total type="integer">2004</total>
<used type="integer">874</used>
<free type="integer">980</free>
</available_ram>
</pre>

*Containers: missing_ganeti and missing_db*

Here the names of the missing machines are provided in the simple form.
The former container describes machines missing in the Ganeti, while the
former contains the machines missing in the database.

Example:
<pre>
<missing_db type="list">
<value>3429_test</value>
<value>breakthis.gwm.osuosl.org</value>
<value>brookjon.gwm.osuosl.org</value>
<value>noinstall2.gwm.osuosl.org</value>
</missing_db>
</pre>

*Container: quota and default_quota*

This container returns the quotas for the user performing request. If
the user is not found or do not have a quotas assigned, default quota is
returned.
If there are no values for the specific quota element, null is returned.
Default_quota container is additionally returned for the case that quota
for the user if found.

|_. Name |_. Type |_. Description |
|<code>default</code> | <code>Integer</code> | Used if default quota is
returned|
|<code>virtual_cpus</code> | <code>Integer</code> | Virtual CPUs|
|<code>ram</code>|<code>Integer</code>|Amount of RAM available to the
user|
|<code>disk</code>|<code>Integer</code>|Amount of disk available to the
user|

Example:
<pre>
<quota type="hash">
<default type="integer">1</default>
<virtual_cpus type="null"/>
<ram type="null"/>
<disk type="null"/>
</quota>
</pre>

*Container: info*

This element provides extensive information related to the cluster.
These information are used internally in Ganeti Web Manager to render
specific pages. As of level of detail used, the field contained here
will not be described but just provided in detail in example.

::

<pre>
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
</pre>

h2. /api/node

In this endpoint exposed are the attributes and operations on the
Cluster.

|_. Name |_. Type |_. ReadOnly |_. Nullable |_. Description |_.
|<code>info</code>|<code>list</code>|=. x| |This complex field returns
various information related to the node.|
|<code>ram_free</code>|<code>integer</code>|=. x| |Integer data. Ex:
2673|
|<code>Admin</code>|<code>boolean</code>|=. x| |Determines if the user
has admin status on the node|
|<code>hostname</code>|<code>string</code>|=. x| |Hostname of the node|
|<code>modify</code>|<code>boolean</code>|=. x| |Determines if the user
is able to modify node parameters|
|<code>cluster</code>|<code>related</code>|=. x| |Cluster the node
belongs to|
|<code>disk_total</code>|<code>integer</code>| | |Integer data. Ex:
2673|
|<code>node_count</code>|<code>Integer</code>|=. x| |Number of the nodes
in the cluster|
|<code>last_job</code>|<code>related</code>| |=. x|A single related
resource. Can be either a URI or set of nested resource data.|
|<code>disk_free</code>|<code>integer</code>|=. x| |Integer data. Ex:
2673|
|<code>ram_total</code>|<code>integer</code>|=. x| |Integer data. Ex:
2673|
|<code>role</code>|<code>string</code>|=. x| |Unicode string data. Ex:
"Hello World"|
|<code>offline</code>|<code>boolean</code>|=. x| |Boolean data. Ex:
True|
|<code>id</code>|<code>string</code>|=. x| |Unicode string data. Ex:
"Hello World"|
|<code>primary_list</code>|<code>list</code>|=. x|=. x |List of virtual
machines (primary node). Contains vm link (related) and hostname for
particular object.|
|<code>secondary_list</code>|<code>list</code>|=. x|=. x |List of
virtual machines (secondary node). Contains vm link (related) and
hostname for particular object.|
|<code>actions_on_node</code>|<code>list</code>|=. x| |Returns the
actions done on the node. The list is composed of objects, containing
elements as described here.|
|<code>resource_uri</code>|<code>string</code>|=. x| |Unicode string
data. Ex: "Hello World"|

*Container: actions_on_node*

This container provides the actions done on the node in form of the log.
It is similar in the form to the other actions_on_X containers in other
endpoints. For more info please take a look there.

*Container: primary_list and secondary_list*

These containers provide the list of virtual machines existing on the
node in primary and secondary node mode.
The list is simple and includes object hostname and related link.
Example::

    <pre>
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
    </pre>

*Container: info*

This element provides extensive information related to the node. These
information are used internally in Ganeti Web Manager to render specific
pages. As of level of detail used, the field contained here will be
described partially only. It should be noted that the elements in the
table may be nullable. The full example output is included after the
table.

|_. Name |_. Type |_. Description |
|<code>pinst_cnt</code> | <code>Integer</code> | Number of virtual
machines for which the node is primary|
|<code>sinst_cnt</code> | <code>Integer</code> | Number of virtual
machines for which the node is secondary|
|<code>pinst_list</code> | <code>List</code> | Virtual machines on this
node (primary)|
|<code>sinst_list</code> | <code>List</code> | Virtual machines on this
node (secondary)|
|<code>drained</code> | <code>Boolean</code> | Determines if the node is
drained|
|<code>offline</code> | <code>Boolean</code> | Determines if the node is
ofline|
|<code>vm_capable</code> | <code>Boolean</code> | Determines if the node
is capable of hosting virtual machines|
|<code>master_capable</code> | <code>Boolean</code> | Determines if the
node is capable to become master node|
|<code>master_candidate</code> | <code>Boolean</code> | Determines if
the node is master candidate|
|<code>mnode</code> | <code>Boolean</code> | Determines if the node is
active master node|
|<code>pip</code> | <code>String</code> | Primary IP address of the
node|
|<code>sip</code> | <code>String</code> | Secondary IP address of the
node|
|<code>uuid</code> | <code>String</code> | UUID|
|<code>group.uuid</code> | <code>String</code> |group UUID|
|<code>tags</code> | <code>List</code> | Tags attached to the node|

::

    <pre>
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
    </pre>


h2. /api/job

This endpoint exposes information related to the job execution in the
system.

|_. Name |_. Type |_. ReadOnly |_. Nullable |_. Description |_.
|<code>status</code>|<code>string</code>| | |Unicode string data. Ex:
"Hello World"|
|<code>summarys</code>|<code>string</code>|=. x|=. x|Describes the job
summary.|
|<code>job_id</code>|<code>integer</code>| | |Integer data. Ex: 2673|
|<code>cluster_admin</code>|<code>Boolean</code>|=. x| |Determines if
the current user has admin permissions over related cluster.|
|<code>ops</code>|<code>list</code>|=. x| |Complex field containing
details about job. The field contents depend on the job type. More
details can be found in the wiki.|
|<code>opresult</code>|<code>list</code>|=. x|=. x|Describes the error
occurred during job execution.|
|<code>cluster</code>|<code>related</code>| | |A single related
resource. Can be either a URI or set of nested resource data.|
|<code>finished</code>|<code>datetime</code>| |=. x|A date & time as a
string. Ex: "2010-11-10T03:07:43"|
|<code>cleared</code>|<code>boolean</code>| | |Boolean data. Ex: True|
|<code>resource_uri</code>|<code>string</code>| | |Unicode string data.
Ex: "Hello World"|

*Container: opresult*

This field contains a detailed description of error encountered during
job execution.
The fields included are the following:

|_. Name |_. Type |_. Description |_.
|error_type|string|Denotes the type of the error|
|error_message|string|Contains a summary description of the error. May
be omitted.|
|error_family|string|Relates error to the family of errors. May be
omitted.|

Example::

    <pre>
    <opresult type="hash">
    <error_type>OpPrereqError</error_type>
    <error_message>The given name (owelwjqe) does not resolve: Name or
    service not known</error_message>
    <error_family>resolver_error</error_family>
    </opresult>
    </pre>

*Container: ops*
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
