import copy
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import verify_public  # noqa: E402


def dns_observation(resolver: str) -> dict:
    return {
        "resolver": resolver,
        "answers": {
            "NS": {
                "records": [
                    {"value": "aria.ns.cloudflare.com."},
                    {"value": "miles.ns.cloudflare.com."},
                ]
            },
            "DS": {"records": [{"value": "12345 13 2 ABCDEF"}]},
        },
        "dnssec": {"ok": True, "status": "NOERROR", "ad": True},
    }


def valid_report() -> dict:
    origin = "https://example.com"
    return {
        "dns": [dns_observation("1.1.1.1"), dns_observation("8.8.8.8")],
        "http": {
            "/": {
                "ok": True,
                "status": 200,
                "final_url": origin + "/",
                "body": f'<link rel="canonical" href="{origin}/">',
            },
            "/guide/": {
                "ok": True,
                "status": 200,
                "final_url": origin + "/guide/",
                "body": "Guide",
            },
            "/robots.txt": {
                "ok": True,
                "status": 200,
                "final_url": origin + "/robots.txt",
                "body": f"Sitemap: {origin}/sitemap.xml",
            },
            "/sitemap.xml": {
                "ok": True,
                "status": 200,
                "final_url": origin + "/sitemap.xml",
                "body": f"<urlset><url><loc>{origin}/</loc></url></urlset>",
            },
        },
    }


class PublicVerificationTest(unittest.TestCase):
    def test_complete_recorded_fixture_passes(self) -> None:
        result = verify_public.evaluate_report(
            valid_report(),
            "https://example.com",
            ["/guide/"],
            require_cloudflare_ns=True,
            require_dnssec=True,
        )
        self.assertTrue(result["summary"]["ok"], result)

    def test_dnssec_ad_requires_successful_validated_response(self) -> None:
        report = valid_report()
        report["dns"][1]["dnssec"] = {"ok": False, "status": "SERVFAIL", "ad": True}
        result = verify_public.evaluate_report(
            report,
            "https://example.com",
            ["/guide/"],
            require_cloudflare_ns=True,
            require_dnssec=True,
        )
        self.assertIn("dnssec_ad", result["summary"]["failures"])

    def test_resolver_disagreement_is_not_completion(self) -> None:
        report = copy.deepcopy(valid_report())
        report["dns"][1]["answers"]["DS"]["records"][0]["value"] = "54321 13 2 FEDCBA"
        result = verify_public.evaluate_report(
            report,
            "https://example.com",
            ["/guide/"],
            require_cloudflare_ns=True,
            require_dnssec=True,
        )
        self.assertIn("parent_ds", result["summary"]["failures"])

    def test_representative_route_cannot_silently_redirect_to_root(self) -> None:
        report = valid_report()
        report["http"]["/guide/"]["final_url"] = "https://example.com/"
        result = verify_public.evaluate_report(
            report,
            "https://example.com",
            ["/guide/"],
            require_cloudflare_ns=True,
            require_dnssec=True,
        )
        self.assertIn("representative_paths", result["summary"]["failures"])

    def test_https_cannot_downgrade_to_http(self) -> None:
        report = valid_report()
        report["http"]["/"]["final_url"] = "http://example.com/"
        report["http"]["/guide/"]["final_url"] = "http://example.com/guide/"
        result = verify_public.evaluate_report(
            report,
            "https://example.com",
            ["/guide/"],
            require_cloudflare_ns=True,
            require_dnssec=True,
        )
        self.assertIn("https_root", result["summary"]["failures"])
        self.assertIn("representative_paths", result["summary"]["failures"])

    def test_robots_requires_exact_sitemap_url(self) -> None:
        report = valid_report()
        report["http"]["/robots.txt"]["body"] = "Sitemap: https://example.com/sitemap.xml.evil"
        result = verify_public.evaluate_report(
            report,
            "https://example.com",
            ["/guide/"],
            require_cloudflare_ns=True,
            require_dnssec=True,
        )
        self.assertIn("robots", result["summary"]["failures"])

    def test_saas_profile_can_mark_absent_canonical_and_seo_files_not_required(self) -> None:
        report = valid_report()
        report["http"]["/"]["body"] = "SaaS application"
        report["http"].pop("/robots.txt")
        report["http"].pop("/sitemap.xml")
        result = verify_public.evaluate_report(
            report,
            "https://example.com",
            ["/guide/"],
            require_cloudflare_ns=True,
            require_dnssec=True,
            allow_missing_canonical=True,
            allow_missing_seo_files=True,
        )
        self.assertTrue(result["summary"]["ok"], result)
        statuses = {item["name"]: item["status"] for item in result["checks"]}
        self.assertEqual(statuses["canonical_origin"], "not_required")
        self.assertEqual(statuses["robots"], "not_required")
        self.assertEqual(statuses["sitemap"], "not_required")

    def test_optional_canonical_still_rejects_a_wrong_present_value(self) -> None:
        report = valid_report()
        report["http"]["/"]["body"] = '<link rel="canonical" href="https://wrong.example/">'
        result = verify_public.evaluate_report(
            report,
            "https://example.com",
            ["/guide/"],
            require_cloudflare_ns=True,
            require_dnssec=True,
            allow_missing_canonical=True,
            allow_missing_seo_files=False,
        )
        self.assertIn("canonical_origin", result["summary"]["failures"])

    def test_malformed_observations_fail_closed_without_crashing(self) -> None:
        result = verify_public.evaluate_report(
            {"dns": [None, {"resolver": "1.1.1.1", "answers": {"NS": {"records": [{}]}}}], "http": None},
            "https://example.com",
            ["/guide/"],
            require_cloudflare_ns=True,
            require_dnssec=True,
        )
        self.assertFalse(result["summary"]["ok"])

    def test_invalid_domain_is_rejected(self) -> None:
        for value in ("localhost", "127.0.0.1", "bad host", "example.local"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                verify_public.validate_domain(value)

    def test_resolvers_must_be_distinct_and_public(self) -> None:
        for value in ("", "localhost", "127.0.0.1", "192.168.1.1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                verify_public.validate_resolver(value)
        with self.assertRaisesRegex(ValueError, "at least two distinct"):
            verify_public.run_verification(
                "example.com",
                "https://example.com",
                ["/guide/"],
                ["1.1.1.1", "1.1.1.1"],
                1,
                False,
                False,
            )

    def test_representative_path_rejects_external_or_traversal_values(self) -> None:
        for value in ("https://other.example/page", "//other.example/page", "/../admin", "/guide?preview=1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                verify_public.run_verification(
                    "example.com",
                    "https://example.com",
                    [value],
                    [],
                    1,
                    False,
                    False,
                )


if __name__ == "__main__":
    unittest.main()
