# Coding: utf-8
from pyramid import testing
import unittest


class ViewsTest(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_main_page(self):
        from ajpmanager.views import MainPage
        self.config.testing_securitypolicy(userid='Vasya',
            permissive=True) # This permissive does not work in our code
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        response = MainPage(request).__call__()
        self.assertEqual(response['username'], 'Vasya')

    def test_json_processor(self):
        from ajpmanager.views import JSONprocessor
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        request.json_body = {'query': 'put that cookie down!'}
        response = JSONprocessor(request).mainline()
        self.assertEqual(response['answer'], 'Wrong query')
        self.assertEqual(response['status'], False)


class IPFiltersTest(unittest.TestCase):

    admin_login = '/login?login=admin&password=admin'\
                  '&came_from=MainPage&form.submitted=Login'

    def setUp(self):
        from ajpmanager import main
        app = main(None, **{'ajp.allowed_ips': '*', 'ajp.vm_provider': 'kvm'})
        from webtest import TestApp
        self.testapp = TestApp(app)
        from ajpmanager.core.DBConnector import DBConnection
        db = DBConnection()
        db.io.expire('allowed_ips', 0)
        db.io.rpush('allowed_ips', '999.999.999.999')

    def test_login_page_ip_filter(self):
        self.testapp.get(self.admin_login, status=403, extra_environ=dict(REMOTE_ADDR='127.0.0.1'))
        self.testapp.get('/login', status=403, extra_environ=dict(REMOTE_ADDR='127.0.0.1'))
        self.testapp.get('/', status=403, extra_environ=dict(REMOTE_ADDR='127.0.0.1'))

    def test_root_page_ip_filter(self):
        self.testapp.get(self.admin_login, status=302, extra_environ=dict(REMOTE_ADDR='999.999.999.999'))
        res = self.testapp.get('/', status=403, extra_environ=dict(REMOTE_ADDR='127.0.0.1'))

    def test_logout_page_ip_filter(self):
        self.testapp.get('/logout', status=403, extra_environ=dict(REMOTE_ADDR='127.0.0.1')) # plain logout
        self.testapp.get(self.admin_login, status=302, extra_environ=dict(REMOTE_ADDR='999.999.999.999'))
        res = self.testapp.get('/logout', status=403, extra_environ=dict(REMOTE_ADDR='127.0.0.1')) # authed + logout

    def test_ajax_processor_ip_filter(self):
        res = self.testapp.post('/engine.ajax', status=403, extra_environ=dict(REMOTE_ADDR='127.0.0.1'))
        res = self.testapp.get('/engine.ajax', status=403, extra_environ=dict(REMOTE_ADDR='127.0.0.1'))



class JSONFunctionsUnitTest(unittest.TestCase):
    """
    Tests for:
                 - verify_new_vm_name,
                 - get_vms_list,
                 - get_presets_list,
                 - machines_control,
                 - get_storage_info
                 - get_settings
                 - apply_settings
                 - restore_default_settings
                 - create_vnc_connection
                 - release_vnc_connection
    """

    def setUp(self):
        self.config = testing.setUp()
        from ajpmanager.core.DBConnector import DBConnection
        db = DBConnection()
        db.io.expire('allowed_ips', 0)
        db.io.rpush('allowed_ips', '*')

    def tearDown(self):
        testing.tearDown()

    def test_verify_new_vm_name(self):
        from ajpmanager.views import JSONprocessor
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        request.json_body = {'query': 'verify_new_vm_name!'}
        response = JSONprocessor(request).mainline()
        self.failUnless(type(response) is dict)


class ViewsFunctionalTests(unittest.TestCase):

    admin_login = '/login?login=admin&password=admin'\
                   '&came_from=MainPage&form.submitted=Login'

    def setUp(self):
        from ajpmanager import main
        app = main(None, **{'ajp.allowed_ips': '*', 'ajp.vm_provider': 'kvm'})
        from webtest import TestApp
        self.testapp = TestApp(app)

    def test_root_login_redirect(self):
        res = self.testapp.get('/', status=200)
        self.failUnless('login' in res.body)
        self.failUnless('password' in res.body)