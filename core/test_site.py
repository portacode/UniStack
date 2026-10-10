import json
from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import TestCase, SimpleTestCase, override_settings
from core.branding import get_brand, contrast_text
from scripts.configure_branding import configure


class BrandingTests(SimpleTestCase):
    def test_deployment_inputs_persist_and_validate(self):
        with TemporaryDirectory() as folder:
            configure(folder, {"BRAND_NAME": "Papertrail", "BRAND_PRIMARY": "#123456", "BRAND_ACCENT": "#ffffff"})
            configure(folder, {})  # Reruns preserve the chosen brand.
            with override_settings(BASE_DIR=Path(folder)):
                brand = get_brand()
                self.assertEqual(brand["name"], "Papertrail")
                self.assertEqual(brand["primary"], "#123456")
                self.assertEqual(brand["accent_text"], "#111827")
            with self.assertRaises(ValueError):
                configure(folder, {"BRAND_PRIMARY": "red;}</style><script>"})
            logo = Path(folder) / "unsafe.svg"
            logo.write_text('<svg onload="alert(1)"/>')
            with self.assertRaises(ValueError):
                configure(folder, {"BRAND_LOGO": str(logo)})

    def test_uploaded_logo_is_copied_to_public_static_asset(self):
        with TemporaryDirectory() as folder:
            import io
            from PIL import Image
            output = io.BytesIO()
            Image.new("RGB", (20, 20), "red").save(output, "PNG")
            source = Path(folder) / "upload"
            source.write_bytes(output.getvalue())
            configure(folder, {"BRAND_LOGO": str(source)})
            brand = json.loads((Path(folder) / "branding.json").read_text())
            self.assertEqual((Path(folder) / "core/static" / brand["logo"]).read_bytes(), source.read_bytes())

    def test_contrast_chooses_readable_foreground(self):
        self.assertEqual(contrast_text("#ffffff"), "#111827")
        self.assertEqual(contrast_text("#000000"), "#ffffff")


class SiteTests(TestCase):
    def test_overview_is_project_agnostic_and_chat_is_lazy(self):
        response = self.client.get("/")
        self.assertContains(response, 'data-nav')
        self.assertNotContains(response, '<unicom-chat-with-sidebar')
        self.assertNotContains(response, 'webchat-with-sidebar.js')
        self.assertNotContains(response, 'UniStack')
        self.assertNotContains(response, 'Portacode')

    @override_settings(UNISTACK_ALLOW_ANONYMOUS_CHAT=True)
    def test_brand_on_all_pages_and_escaped(self):
        with TemporaryDirectory() as folder:
            configure(folder, {"BRAND_NAME": '<Paper & Co>', "BRAND_PRIMARY": "#aabbcc"})
            with override_settings(BASE_DIR=Path(folder)):
                for url in ("/", "/assistant/", "/accounts/login/"):
                    response = self.client.get(url)
                    self.assertContains(response, '&lt;Paper &amp; Co&gt;')
                    self.assertContains(response, '--brand-primary: #aabbcc')

    def test_non_staff_user_can_sign_in_and_logout(self):
        from django.contrib.auth import get_user_model
        get_user_model().objects.create_user(username="member", password="a-test-password")
        response = self.client.post('/accounts/login/', {"username": "member", "password": "a-test-password"})
        self.assertRedirects(response, '/assistant/')
        self.assertNotContains(self.client.get('/assistant/'), 'href="/admin/"')
        self.assertEqual(self.client.get('/accounts/logout/').status_code, 405)
        self.assertRedirects(self.client.post('/accounts/logout/'), '/')
