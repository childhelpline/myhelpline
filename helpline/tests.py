"""Test Cases for the Helpline application"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from helpline.models import Case, Hotdesk
from helpline.forms import QueueLogForm
from helpline.forms import LoginForm
from helpline.views import initialize_myaccount


class AgentTestCase(TestCase):
    fixtures = ['helpline/fixtures/helpline.json']

    def setUp(self):
        self.user = User.objects.create_user(username="user_test",
                                             password="password_test")

    def testFixture(self):
        """Check if inital data can be loaded correctly"""
        self.assertEqual(
            Hotdesk.objects.all().count(), 15
        )

    def test_login(self):
        """Test login user"""
        response = self.client.login(username=self.user.username,
                                     password='password_test')
        self.assertTrue(response)

    def test_login_fail(self):
        """Test fail login user"""
        response = self.client.login(username=self.user.username,
                                     password='test_password')
        self.assertFalse(response)

    def test_login_form(self):
        form_data = {'username': self.user.username,
                     'password': 'test_password'}
        form = LoginForm(data=form_data)
        self.assertEqual(form.is_valid(), True)

    def test_login_page_form(self):
        """Test login user"""
        response = self.client.post(reverse('login'),
                                    {'username': self.user.username,
                                     'password': 'password_test'})
        self.assertTrue(response)

    def test_login_page_form_fail(self):
        """Test fail login user"""
        response = self.client.post(reverse('login'),
                                    {'username': self.user.username,
                                     'password': 'password_fail'})
        self.assertTrue(response)

    def test_initialize_myaccount(self):
        """Test account initialization"""
        initialize_myaccount(self.user)

    def test_queue_join(self):
        """Test joining queue"""
        response = self.client.post(reverse('queue_log'),
                                    {'extension': '8010'})
        self.assertTrue(response)

    def test_queue_log_form(self):
        form_data = {'softphone': '8010'}
        form = QueueLogForm(data=form_data)
        self.assertEqual(form.is_valid(), True)


class CaseCreateTestCase(TestCase):
    def createCase(self):
        Case.objects.create(hl_key="", hl_user="")
        Case.objects.create(hl_key="", hl_user="")

    def test_call_form(self):
        """Test if form popup will show on case create"""
        pass


class QueueManageTestCase(TestCase):
    def join_queue(self):
        """Test joining the queue"""
        pass

    def leave_queue(self):
        """Test leaving the queue"""
        pass

    def pause_queue(self):
        """Test pausing user on the queue"""
        pass

    def unpause_queue(self):
        """Test unpausing user on the queue"""
        pass


class AccountManageTestCase(TestCase):
    def update_profile(self):
        pass

    def add_avatar(self):
        pass


class InboundCallTestCase(TestCase):
    def join_queue(self):
        """Test joining the queue"""
        pass

    def create_call_file(self):
        """Test creating the call file using PyCall"""
        pass

    def check_cdr_update(self):
        """Check for updated CDR Records. Update done by PBX."""
        pass

    def simulate_call_pickup(self):
        """Simulate Agent answer."""
        pass

    def check_form_popup(self):
        """Validate form pop up."""
        pass

    def update_caller_info(self):
        """Update caller info on case."""
        pass

    def leave_queue(self):
        """Test leave queue."""
        pass
