from unittest import TestCase

from ganeti_web.caps import (ANCIENT, FUTURE, GANETI22, GANETI24, GANETI242,
                             GANETI25, classify, has_cdrom2,
                             has_shutdown_timeout, has_balloonmem)

class Mock(object):
    pass

def make_mock_cluster(version):
    cluster = Mock()
    cluster.info = {"software_version": version}
    return cluster


class TestClassify(TestCase):

    def test_ancient(self):
        cluster = make_mock_cluster("2.1.0")
        self.assertEqual(classify(cluster), ANCIENT)

    def test_future(self):
        cluster = make_mock_cluster("3.0.0")
        self.assertEqual(classify(cluster), FUTURE)

    def test_ganeti22(self):
        cluster = make_mock_cluster("2.2.0")
        self.assertEqual(classify(cluster), GANETI22)

    def test_ganeti242(self):
        cluster = make_mock_cluster("2.4.2")
        self.assertEqual(classify(cluster), GANETI242)

    def test_ganeti241(self):
        cluster = make_mock_cluster("2.4.1")
        self.assertEqual(classify(cluster), GANETI24)

    def test_ganeti25(self):
        cluster = make_mock_cluster("2.5.0")
        self.assertEqual(classify(cluster), GANETI25)


class TestHasShutdownTimeout(TestCase):

    def test_has_shutdown_timeout(self):
        cluster = make_mock_cluster("2.5.0")
        self.assertTrue(has_shutdown_timeout(cluster))

    def test_lacks_shutdown_timeout(self):
        cluster = make_mock_cluster("2.4.0")
        self.assertFalse(has_shutdown_timeout(cluster))


class TestHasCdrom2(TestCase):

    def test_has_cdrom2(self):
        cluster = make_mock_cluster("2.5.0")
        self.assertTrue(has_cdrom2(cluster))

    def test_lacks_cdrom2(self):
        cluster = make_mock_cluster("2.2.0")
        self.assertFalse(has_cdrom2(cluster))

class TestRequiresMaxmem(TestCase):

    # Ganeti >= 2.6 changes the beparam 'memory' to 'maxmem' and 'minmem'
    # however, just using 'maxmem' seems to work.
    def test_has_balloonmem(self):
        cluster = make_mock_cluster("2.6.0")
        self.assertTrue(has_balloonmem(cluster))

    def test_no_balloonmem(self):
        cluster = make_mock_cluster("2.5.0")
        self.assertFalse(has_balloonmem(cluster))
