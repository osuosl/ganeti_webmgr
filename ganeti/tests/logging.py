from django.contrib.auth.models import User
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode

from ganeti.models import Profile, VirtualMachine, Cluster, LogItem, LogAction

class TestLogging(TestCase):
    def setUp(self):
        self.tearDown()

    def tearDown(self):
        Profile.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        LogItem.objects.all().delete()
        LogAction.objects.all().delete()

    def test_log_signal(self):
        """
        Test signals related to LogItem, LogAction:

        Verifies:
            * LogItem, LogAction are created/deleted
        """
        act1 = LogAction(name="start", action_message="started")
        act2 = LogAction(name="stop", action_message="stopped")
        act1.save()
        act2.save()

        self.assertTrue(LogAction.objects.filter(pk=act1.pk).exists())
        self.assertTrue(LogAction.objects.filter(pk=act2.pk).exists())

        user = User(username="testing")
        user.save()
        profile = user.get_profile()
        self.assert_(profile, 'Profile was not created')

        test1 = Cluster(hostname="localhost", slug="localhost")
        test1.save()
        test2 = VirtualMachine(cluster=test1, hostname="localhost1", owner=profile)
        test2.save()

        self.assertTrue(Cluster.objects.filter(id=test1.id).exists())
        self.assertTrue(VirtualMachine.objects.filter(id=test2.id).exists())

        log1 = LogItem(
            action = act1, user = profile,
            object_type = ContentType.objects.get_for_model(test1),
            object_id = test1.pk,
            object_repr = force_unicode(test1),
            log_message = "started test #1",
        )
        log1.save()
        self.assertTrue(LogItem.objects.filter(id=log1.id).exists())

        log2 = LogItem(
            action = act2, user = profile,
            object_type = ContentType.objects.get_for_model(test2),
            object_id = test2.pk,
            object_repr = force_unicode(test2),
            log_message = "stopped test #2"
        )
        log2.save()
        self.assertTrue(LogItem.objects.filter(id=log2.id).exists())

    def test_log_repr(self):
        """
        Test LogItem repr (== log format):

        Verifies:
            * LogItem is created by LogItemManager
        """
        act1 = LogAction(name="start", action_message="started")
        act2 = LogAction(name="stop", action_message="stopped")
        act3 = LogAction(name="deletion", action_message="deleted")
        act1.save()
        act2.save()
        act3.save()

        self.assertTrue(LogAction.objects.filter(pk=act1.pk).exists())
        self.assertTrue(LogAction.objects.filter(pk=act2.pk).exists())

        user = User(username="testing")
        user.save()
        profile = user.get_profile()
        self.assert_(profile, 'Profile was not created')

        test1 = Cluster(hostname="localhost", slug="localhost")
        test1.save()
        test2 = VirtualMachine(cluster=test1, hostname="localhost1", owner=profile)
        test2.save()

        self.assertTrue(Cluster.objects.filter(id=test1.id).exists())
        self.assertTrue(VirtualMachine.objects.filter(id=test2.id).exists())

        pk1 = LogItem.objects.log_action(user=profile, affected_object=test1, action=act1, log_message="started test #1")
        LogItem.objects.log_action(user=profile, affected_object=test2, action="start", log_message="started test #2")
        LogItem.objects.log_action(user=profile, affected_object=test1, action=act2, log_message="stopped test #1")
        pk2 = LogItem.objects.log_action(user=profile, affected_object=test2, action="stop", log_message="stopped test #2")
        pk3 = LogItem.objects.log_action(user=profile, affected_object=profile, action="deletion")

        self.assertEqual(len(LogItem.objects.all()), 5)

        item1 = LogItem.objects.get( pk=pk1 )
        item2 = LogItem.objects.get( pk=pk2 )
        item3 = LogItem.objects.get( pk=pk3 )

        self.assertEqual(repr(item1),
            "[%s] user testing started cluster \"localhost\": started test #1" % item1.timestamp,
        )
        self.assertEqual(repr(item2),
            "[%s] user testing stopped virtual machine \"localhost1\": stopped test #2" % item2.timestamp,
        )
        self.assertEqual(repr(item3),
            "[%s] user testing deleted profile \"testing\"" % item3.timestamp,
        )
