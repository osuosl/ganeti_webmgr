# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Cluster.hostname'
        db.alter_column('clusters_cluster', 'hostname', self.gf('ganeti_webmgr.utils.fields.LowerCaseCharField')(unique=True, max_length=128))

    def backwards(self, orm):

        # Changing field 'Cluster.hostname'
        db.alter_column('clusters_cluster', 'hostname', self.gf('django.db.models.fields.CharField')(max_length=128, unique=True))

    models = {
        'clusters.cluster': {
            'Meta': {'ordering': "['hostname', 'description']", 'object_name': 'Cluster'},
            'cached': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'disk': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'hostname': ('ganeti_webmgr.utils.fields.LowerCaseCharField', [], {'unique': 'True', 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cluster_last_job'", 'null': 'True', 'to': "orm['jobs.Job']"}),
            'mtime': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'password': ('ganeti_webmgr.utils.fields.PatchedEncryptedCharField', [], {'default': "''", 'max_length': '293', 'cipher': "'AES'", 'blank': 'True'}),
            'port': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5080'}),
            'ram': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'virtual_cpus': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'jobs.job': {
            'Meta': {'object_name': 'Job'},
            'cached': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'cluster': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['clusters.Cluster']"}),
            'cluster_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_cache': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'job_id': ('django.db.models.fields.IntegerField', [], {}),
            'mtime': ('ganeti_webmgr.utils.fields.PreciseDateTimeField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '6'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {}),
            'op': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'serialized_info': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['clusters']