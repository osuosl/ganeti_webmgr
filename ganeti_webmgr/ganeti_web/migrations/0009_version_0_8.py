# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding field 'Job.processed'
        db.add_column('ganeti_web_job', 'processed', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Job.op'
        db.add_column('ganeti_web_job', 'op', self.gf('django.db.models.fields.CharField')(default='Unknown', max_length=50), keep_default=False)

        # Changing field 'VirtualMachine.status'
        db.alter_column('ganeti_web_virtualmachine', 'status', self.gf('django.db.models.fields.CharField')(max_length=14))

        # Adding field 'Node.cpus'
        db.add_column('ganeti_web_node', 'cpus', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Changing field 'Cluster.password'
        db.alter_column('ganeti_web_cluster', 'password', self.gf('django_fields.fields.EncryptedCharField')(max_length=293, null=True, cipher='AES'))

        # Deleting field 'VirtualMachineTemplate.nic_mode'
        db.delete_column('ganeti_web_virtualmachinetemplate', 'nic_mode')

        # Deleting field 'VirtualMachineTemplate.disk_size'
        db.delete_column('ganeti_web_virtualmachinetemplate', 'disk_size')

        # Deleting field 'VirtualMachineTemplate.nic_link'
        db.delete_column('ganeti_web_virtualmachinetemplate', 'nic_link')

        # Adding field 'VirtualMachineTemplate.description'
        db.add_column('ganeti_web_virtualmachinetemplate', 'description', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'VirtualMachineTemplate.no_install'
        db.add_column('ganeti_web_virtualmachinetemplate', 'no_install', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'VirtualMachineTemplate.disks'
        db.add_column('ganeti_web_virtualmachinetemplate', 'disks', self.gf('django_fields.fields.PickleField')(null=True, blank=True), keep_default=False)

        # Adding field 'VirtualMachineTemplate.nics'
        db.add_column('ganeti_web_virtualmachinetemplate', 'nics', self.gf('django_fields.fields.PickleField')(null=True, blank=True), keep_default=False)

        # Adding field 'VirtualMachineTemplate.cdrom2_image_path'
        db.add_column('ganeti_web_virtualmachinetemplate', 'cdrom2_image_path', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True), keep_default=False)

        # Adding unique constraint on 'VirtualMachineTemplate', fields ['cluster', 'template_name']
        db.create_unique('ganeti_web_virtualmachinetemplate', ['cluster_id', 'template_name'])


    def backwards(self, orm):

        # Removing unique constraint on 'VirtualMachineTemplate', fields ['cluster', 'template_name']
        db.delete_unique('ganeti_web_virtualmachinetemplate', ['cluster_id', 'template_name'])

        # Deleting field 'Job.processed'
        db.delete_column('ganeti_web_job', 'processed')

        # Deleting field 'Job.op'
        db.delete_column('ganeti_web_job', 'op')

        # Changing field 'VirtualMachine.status'
        db.alter_column('ganeti_web_virtualmachine', 'status', self.gf('django.db.models.fields.CharField')(max_length=10))

        # Deleting field 'Node.cpus'
        db.delete_column('ganeti_web_node', 'cpus')

        # Changing field 'Cluster.password'
        db.alter_column('ganeti_web_cluster', 'password', self.gf('django.db.models.fields.CharField')(max_length=128, null=True))

        # Adding field 'VirtualMachineTemplate.nic_mode'
        db.add_column('ganeti_web_virtualmachinetemplate', 'nic_mode', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'VirtualMachineTemplate.disk_size'
        db.add_column('ganeti_web_virtualmachinetemplate', 'disk_size', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'VirtualMachineTemplate.nic_link'
        db.add_column('ganeti_web_virtualmachinetemplate', 'nic_link', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Deleting field 'VirtualMachineTemplate.description'
        db.delete_column('ganeti_web_virtualmachinetemplate', 'description')

        # Deleting field 'VirtualMachineTemplate.no_install'
        db.delete_column('ganeti_web_virtualmachinetemplate', 'no_install')

        # Deleting field 'VirtualMachineTemplate.disks'
        db.delete_column('ganeti_web_virtualmachinetemplate', 'disks')

        # Deleting field 'VirtualMachineTemplate.nics'
        db.delete_column('ganeti_web_virtualmachinetemplate', 'nics')

        # Deleting field 'VirtualMachineTemplate.cdrom2_image_path'
        db.delete_column('ganeti_web_virtualmachinetemplate', 'cdrom2_image_path')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ganeti_web.cluster': {
            'Meta': {'ordering': "['hostname', 'description']", 'object_name': 'Cluster'},
            'cached': ('utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'disk': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cluster_last_job'", 'null': 'True', 'to': "orm['ganeti_web.Job']"}),
            'mtime': ('utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'password': ('django_fields.fields.EncryptedCharField', [], {'max_length': '293', 'null': 'True', 'cipher': "'AES'", 'blank': 'True'}),
            'port': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5080'}),
            'ram': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'virtual_cpus': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'ganeti_web.cluster_perms': {
            'Meta': {'object_name': 'Cluster_Perms'},
            'admin': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'create_vm': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'export': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Cluster_gperms'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'migrate': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'operms'", 'to': "orm['ganeti_web.Cluster']"}),
            'replace_disks': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tags': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Cluster_uperms'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'ganeti_web.clusteruser': {
            'Meta': {'object_name': 'ClusterUser'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'real_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'})
        },
        'ganeti_web.ganetierror': {
            'Meta': {'ordering': "('-timestamp', 'code', 'msg')", 'object_name': 'GanetiError'},
            'cleared': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti_web.Cluster']"}),
            'code': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msg': ('django.db.models.fields.TextField', [], {}),
            'obj_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'obj_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ganeti_errors'", 'to': "orm['contenttypes.ContentType']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'ganeti_web.job': {
            'Meta': {'object_name': 'Job'},
            'cached': ('utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cleared': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['ganeti_web.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'job_id': ('django.db.models.fields.IntegerField', [], {}),
            'mtime': ('utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {}),
            'op': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'ganeti_web.node': {
            'Meta': {'object_name': 'Node'},
            'cached': ('utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'nodes'", 'to': "orm['ganeti_web.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'cpus': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'disk_free': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'disk_total': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti_web.Job']", 'null': 'True'}),
            'mtime': ('utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'offline': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ram_free': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'ram_total': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'})
        },
        'ganeti_web.organization': {
            'Meta': {'object_name': 'Organization', '_ormbases': ['ganeti_web.ClusterUser']},
            'clusteruser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['ganeti_web.ClusterUser']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'organization'", 'unique': 'True', 'to': "orm['auth.Group']"})
        },
        'ganeti_web.profile': {
            'Meta': {'object_name': 'Profile', '_ormbases': ['ganeti_web.ClusterUser']},
            'clusteruser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['ganeti_web.ClusterUser']", 'unique': 'True', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'ganeti_web.quota': {
            'Meta': {'object_name': 'Quota'},
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'quotas'", 'to': "orm['ganeti_web.Cluster']"}),
            'disk': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ram': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'quotas'", 'to': "orm['ganeti_web.ClusterUser']"}),
            'virtual_cpus': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'})
        },
        'ganeti_web.sshkey': {
            'Meta': {'object_name': 'SSHKey'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ssh_keys'", 'to': "orm['auth.User']"})
        },
        'ganeti_web.testmodel': {
            'Meta': {'object_name': 'TestModel'},
            'cached': ('utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti_web.Cluster']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mtime': ('utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'})
        },
        'ganeti_web.virtualmachine': {
            'Meta': {'ordering': "['hostname']", 'unique_together': "(('cluster', 'hostname'),)", 'object_name': 'VirtualMachine'},
            'cached': ('utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'default': '0', 'related_name': "'virtual_machines'", 'to': "orm['ganeti_web.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'disk_size': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti_web.Job']", 'null': 'True'}),
            'mtime': ('utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'operating_system': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'virtual_machines'", 'null': 'True', 'to': "orm['ganeti_web.ClusterUser']"}),
            'pending_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'primary_node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'primary_vms'", 'null': 'True', 'to': "orm['ganeti_web.Node']"}),
            'ram': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'secondary_node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'secondary_vms'", 'null': 'True', 'to': "orm['ganeti_web.Node']"}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '14'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'instances'", 'null': 'True', 'to': "orm['ganeti_web.VirtualMachineTemplate']"}),
            'virtual_cpus': ('django.db.models.fields.IntegerField', [], {'default': '-1'})
        },
        'ganeti_web.virtualmachine_perms': {
            'Meta': {'object_name': 'VirtualMachine_Perms'},
            'admin': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'VirtualMachine_gperms'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modify': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'operms'", 'to': "orm['ganeti_web.VirtualMachine']"}),
            'power': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'remove': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tags': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'VirtualMachine_uperms'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'ganeti_web.virtualmachinetemplate': {
            'Meta': {'unique_together': "(('cluster', 'template_name'),)", 'object_name': 'VirtualMachineTemplate'},
            'boot_order': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cdrom2_image_path': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'cdrom_image_path': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ganeti_web.Cluster']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'disk_template': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'disk_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'disks': ('django_fields.fields.PickleField', [], {'null': 'True', 'blank': 'True'}),
            'iallocator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'iallocator_hostname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kernel_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'memory': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name_check': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'nic_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'nics': ('django_fields.fields.PickleField', [], {'null': 'True', 'blank': 'True'}),
            'no_install': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'os': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pnode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'root_path': ('django.db.models.fields.CharField', [], {'default': "'/'", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'serial_console': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'snode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'template_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'vcpus': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['ganeti_web']
