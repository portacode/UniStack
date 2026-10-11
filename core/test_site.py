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
    def test_public_shell_survives_invite_only_configuration(self):
        from django.core.management import call_command
        call_command("check_site")
        with override_settings(UNISTACK_ALLOW_SIGNUP=False):
            for url in ("/", "/accounts/login/", "/assistant/"):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'href="/accounts/signup/"')
            self.assertEqual(self.client.get("/accounts/signup/").status_code, 404)
            self.assertEqual(self.client.post("/accounts/signup/", {}).status_code, 404)

    def test_bottom_navigation_follows_visible_entry_count(self):
        for count in (1, 5, 6):
            navigation = [{"label": f"Page {i}", "url": f"/page-{i}/"} for i in range(count)]
            with override_settings(SITE_NAVIGATION=navigation):
                response = self.client.get("/")
                self.assertEqual(response.context["mobile_bottom_nav"], count <= 5)
        navigation[-1]["authenticated"] = True
        with override_settings(SITE_NAVIGATION=navigation):
            response = self.client.get("/")
            self.assertTrue(response.context["mobile_bottom_nav"])
            self.assertEqual(len(response.context["site_navigation"]), 5)

    def test_signup_policy_persists_from_deployment(self):
        import os
        import subprocess
        import sys
        from django.conf import settings
        with TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text("UNISTACK_ALLOW_SIGNUP=true\n")
            env = {**os.environ, "UNISTACK_ALLOW_SIGNUP": "false"}
            command = [sys.executable, str(settings.BASE_DIR / "scripts/configure_env.py"), str(path)]
            subprocess.run(command, env=env, check=True, capture_output=True)
            self.assertIn("UNISTACK_ALLOW_SIGNUP=false", path.read_text())
            env.pop("UNISTACK_ALLOW_SIGNUP")
            subprocess.run(command, env=env, check=True, capture_output=True)
            self.assertIn("UNISTACK_ALLOW_SIGNUP=false", path.read_text())

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
        from django.conf import settings
        get_user_model().objects.create_user(username="member", password="a-test-password")
        response = self.client.post('/accounts/login/', {"username": "member", "password": "a-test-password"})
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)
        self.assertNotContains(self.client.get('/assistant/'), 'href="/admin/"')
        self.assertEqual(self.client.get('/accounts/logout/').status_code, 405)
        self.assertRedirects(self.client.post('/accounts/logout/'), '/')
