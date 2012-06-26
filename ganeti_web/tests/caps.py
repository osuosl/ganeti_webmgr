from unittest import TestCase

from ganeti_web.caps import (ANCIENT, FUTURE, GANETI22, GANETI25, classify,
                             has_shutdown_timeout)

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
