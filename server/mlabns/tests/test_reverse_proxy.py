import datetime
import os
import mock
import unittest2

from mlabns.db import model
from mlabns.util import redirect


class RedirectionTest(unittest2.TestCase):

    def setUp(self):
        self.fake_redirect = model.RedirectProbability(
            name="default",
            probability=0.0,
            url="https://mlab-ns.appspot.com")
        redirect._redirect = None

    @mock.patch.object(model, 'RedirectProbability')
    def test_get_redirection_returns_mock_value(self, mock_redirect):
        mock_redirect.return_value.all.return_value.run.return_value = (
            [self.fake_redirect])

        actual = redirect.get_redirection()

        self.assertEqual(actual.name, self.fake_redirect.name)
        self.assertEqual(actual.probability, self.fake_redirect.probability)
        self.assertEqual(actual.url, self.fake_redirect.url)

    @mock.patch.object(model, 'RedirectProbability')
    def test_get_redirection_returns_default_value(self, mock_redirect):
        mock_redirect.return_value.all.return_value.run.return_value = []

        actual = redirect.get_redirection()

        self.assertEqual(actual, redirect.default_redirect)
        self.assertEqual(actual.name, redirect.default_redirect.name)
        self.assertEqual(actual.probability,
                         redirect.default_redirect.probability)
        self.assertEqual(actual.url, redirect.default_redirect.url)

    def test_during_business_hours_returns_true(self):
        t = datetime.datetime(2019, 1, 24, 16, 0, 0)
        self.assertTrue(redirect.during_business_hours(t))

    def test_during_business_hours_with_ignore_environment_returns_true(self):
        t = datetime.datetime(2019, 1, 25, 16, 0, 0)
        os.environ['IGNORE_BUSINESS_HOURS'] = '1'
        self.assertTrue(redirect.during_business_hours(t))
        del os.environ['IGNORE_BUSINESS_HOURS']

    def test_during_business_hours_returns_false(self):
        t = datetime.datetime(2019, 1, 25, 16, 0, 0)
        self.assertFalse(redirect.during_business_hours(t))

    def test_try_redirect_url_when_wrong_path_returns_emptystr(self):
        mock_request = mock.Mock()
        mock_request.path = '/wrong_path'
        t = datetime.datetime(2019, 1, 24, 16, 0, 0)

        url = redirect.try_redirect_url(mock_request, t)

        self.assertEqual(url, "")

    def test_try_redirect_url_when_probability_zero_returns_emptystr(self):
        mock_request = mock.Mock()
        mock_request.path = '/ndt_ssl'
        t = datetime.datetime(2019, 1, 24, 16, 0, 0)
        redirect._redirect = model.RedirectProbability(
            name="default",
            probability=0.0,
            url="https://fake.appspot.com")

        url = redirect.try_redirect_url(mock_request, t)

        self.assertEqual(url, "")

    def test_try_redirect_url_when_outside_business_returns_emptystr(self):
        mock_request = mock.Mock()
        mock_request.path = '/ndt_ssl'
        t = datetime.datetime(2019, 1, 25, 16, 0, 0)
        redirect._redirect = model.RedirectProbability(
            name="default",
            probability=1.0,
            url="https://fake.appspot.com")

        url = redirect.try_redirect_url(mock_request, t)

        self.assertEqual(url, "")

    def test_try_redirect_url_returns_url(self):
        mock_request = mock.Mock()
        mock_request.path = '/ndt_ssl'
        mock_request.path_qs = '/ndt_ssl?format=geo_options'
        t = datetime.datetime(2019, 1, 24, 16, 0, 0)
        redirect._redirect = model.RedirectProbability(
            name="default",
            probability=1.0,
            url="https://fake.appspot.com")

        actual_url = redirect.try_redirect_url(mock_request, t)

        self.assertEqual(actual_url,
                         "https://fake.appspot.com/ndt_ssl?format=geo_options")
