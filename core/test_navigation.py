from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.http import HttpResponse
from django.test import TestCase, RequestFactory, override_settings
from django.urls import path
from django.views.generic import TemplateView
from core.navigation import navigation_for
from core.shell_checks import check_shell, project_page_paths
from config.urls import urlpatterns as site_urls


urlpatterns = [
    path("workspace/", TemplateView.as_view(template_name="core/page.html", extra_context={"page_title": "Workspace"})),
    path("workspace/library/", TemplateView.as_view(template_name="core/page.html", extra_context={"page_title": "Library"})),
    path("broken/", lambda request: HttpResponse('<html><main>A separate app shell</main></html>')),
    *site_urls,
]
NAVIGATION = [
    {"label": "Workspace", "url": "/workspace/", "authenticated": True},
    {"label": "Your library", "mobile_label": "Library", "url": "/workspace/library/", "match": ["/materials/"]},
    {"label": "Assistant", "url": "/assistant/"},
]


@override_settings(ROOT_URLCONF=__name__, SITE_NAVIGATION=NAVIGATION)
class NavigationTests(TestCase):
    def test_only_most_specific_destination_is_active(self):
        request = RequestFactory().get('/workspace/library/42/')
        request.user = SimpleNamespace(is_authenticated=True)
        self.assertEqual([e['url'] for e in navigation_for(request) if e['active']], ['/workspace/library/'])
        request.path = '/materials/42/'
        self.assertEqual([e['url'] for e in navigation_for(request) if e['active']], ['/workspace/library/'])
        request.path = '/workspace/library-other/'
        self.assertEqual([e['url'] for e in navigation_for(request) if e['active']], ['/workspace/'])

    def test_exact_match_and_hidden_entries(self):
        request = RequestFactory().get('/workspace/child/')
        request.user = SimpleNamespace(is_authenticated=False)
        self.assertNotIn('/workspace/', [e['url'] for e in navigation_for(request)])
        request.user.is_authenticated = True
        with override_settings(SITE_NAVIGATION=[{**NAVIGATION[0], 'exact': True}]):
            self.assertFalse(any(e['active'] for e in navigation_for(request)))

    @override_settings(SITE_STYLESHEETS=['product/design.css'])
    def test_product_chat_and_auth_share_navigation_and_assets(self):
        user = get_user_model().objects.create_user(username='shell-tester')
        self.client.force_login(user)
        for url in ['/workspace/', '/workspace/library/', '/assistant/', '/accounts/login/']:
            response = self.client.get(url)
            check_shell(response)
            self.assertContains(response, 'product/design.css')
            self.assertContains(response, 'aria-label="Your library"')
            self.assertContains(response, 'nav-mobile-label')

    def test_deployment_check_rejects_standalone_product_shell(self):
        with override_settings(SITE_NAVIGATION=[{'label': 'Broken', 'url': '/broken/'}]):
            with self.assertRaisesMessage(CommandError, 'extend core/page.html'):
                call_command('check_site')

    def test_signed_in_preflight_checks_private_routes(self):
        get_user_model().objects.create_user(username='shell-tester')
        with override_settings(SITE_NAVIGATION=[{'label': 'Broken', 'url': '/broken/', 'authenticated': True}]):
            call_command('check_site')  # Private page is not requested as guest.
            with self.assertRaisesMessage(CommandError, 'extend core/page.html'):
                call_command('check_site', username='shell-tester')

    def test_shell_guard_rejects_duplicate_navigation(self):
        response = self.client.get('/workspace/')
        response.content += b'<nav id="site-navigation"></nav>'
        with self.assertRaisesMessage(ValueError, 'Expected one #site-navigation'):
            check_shell(response)

    @patch('core.management.commands.check_site.project_page_paths', return_value={'/broken/'})
    def test_unregistered_product_navigation_is_also_rejected(self, paths):
        with self.assertRaisesMessage(CommandError, 'Project route /broken/'):
            call_command('check_site')

    def test_static_routes_in_local_apps_are_discovered(self):
        from django.conf import settings
        app = SimpleNamespace(path=str(settings.BASE_DIR / 'sample'), name=__name__, label='sample')
        with patch('core.shell_checks.apps.get_app_configs', return_value=[app]):
            self.assertIn('/broken/', project_page_paths())
        external = SimpleNamespace(path=str(settings.BASE_DIR / 'apps/sample'), name=__name__, label='sample')
        with patch('core.shell_checks.apps.get_app_configs', return_value=[external]):
            self.assertEqual(project_page_paths(), set())
