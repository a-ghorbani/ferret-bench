"""Two contracts whose silent breakage is expensive.

1. Sampling replicates come from cfg["gen"]["seed"], NOT the harness --seed flag.
   --seed feeds random.Random() for wrapper nonces and tool-call ids only. With
   cfg.gen.seed fixed, llama.cpp is deterministic, so varying --seed produces
   bit-identical turn-0 decisions — i.e. fake replicates. This went unnoticed across
   206 runs and is why no replicate existed before 2026-07-21.

2. cache_key must be stable. A change silently invalidates the entire replay cache
   (~375 MB) and every run stops being reproducible against recorded evidence.
"""
import unittest

from _harness_path import configs, http_cache  # noqa: E402


class TestSeedContract(unittest.TestCase):
    def test_gen_seed_is_present_and_reaches_the_payload(self):
        cfg = configs.load_config("frozen")
        self.assertIn("seed", cfg["gen"], "cfg.gen.seed is the ONLY sampling seed; do not remove it")

    def test_gen_seed_participates_in_config_hash(self):
        """Two configs differing only in gen.seed must be distinguishable runs."""
        a = configs.load_config("rep-s42")
        b = configs.load_config("rep-s43")
        self.assertNotEqual(a["config_hash"], b["config_hash"],
                            "gen.seed must be inside config_hash or replicates are indistinguishable")

    def test_replicate_configs_differ_only_in_seed(self):
        a = configs.load_config("rep-s42")
        b = configs.load_config("rep-s43")
        for k in a:
            if k in ("config_id", "config_hash", "gen"):
                continue
            self.assertEqual(a[k], b[k], f"replicate configs must differ only in gen.seed, but {k} differs")
        self.assertEqual(a["gen"]["temperature"], b["gen"]["temperature"])
        self.assertNotEqual(a["gen"]["seed"], b["gen"]["seed"])


class TestCacheKeyStability(unittest.TestCase):
    # Pinned 2026-07-22 against the live cache. If these change, every recorded
    # response (~375 MB, ~5k files) becomes unreachable and runs stop being replayable.
    BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"
    GOLDEN_NO_BODY = "fe82c6b485fcacb339ff4f3d916f2b02f5231d801f3627641ae0f9dcfcc218a5"
    GOLDEN_WITH_BODY = "40033cc6b6bbae5dba20c37277103e27f15adacd14dc43c32eb0bf902f54a9c4"

    def test_key_is_stable_for_known_input(self):
        self.assertEqual(http_cache.cache_key("brave", "GET", self.BRAVE_URL, None),
                         self.GOLDEN_NO_BODY)
        self.assertEqual(
            http_cache.cache_key("brave", "GET", self.BRAVE_URL, {"q": "nobel prize physics 2026"}),
            self.GOLDEN_WITH_BODY)

    def test_key_is_deterministic_across_calls(self):
        args = ("brave", "GET", "https://x/y", {"q": "nobel prize 2026"})
        self.assertEqual(http_cache.cache_key(*args), http_cache.cache_key(*args))

    def test_method_is_case_normalised(self):
        self.assertEqual(http_cache.cache_key("brave", "get", "https://x/y", None),
                         http_cache.cache_key("brave", "GET", "https://x/y", None))

    def test_body_key_order_does_not_change_key(self):
        """Canonical JSON must sort keys, else identical requests miss the cache."""
        self.assertEqual(http_cache.cache_key("t", "POST", "https://x", {"a": 1, "b": 2}),
                         http_cache.cache_key("t", "POST", "https://x", {"b": 2, "a": 1}))

    def test_different_query_gives_different_key(self):
        self.assertNotEqual(http_cache.cache_key("brave", "GET", "https://x?q=a", None),
                            http_cache.cache_key("brave", "GET", "https://x?q=b", None))

    def test_secrets_are_redacted_before_keying(self):
        """A key must never depend on a credential, or the cache leaks it via the key space."""
        with_key = http_cache.cache_key("t", "POST", "https://x", {"q": "z", "api_key": "SECRET"})
        other_key = http_cache.cache_key("t", "POST", "https://x", {"q": "z", "api_key": "OTHER"})
        self.assertEqual(with_key, other_key, "api_key must be redacted before hashing")


class TestFrozenConfigProvenance(unittest.TestCase):
    FROZEN_HASH = "bbb5cdbf1e9f18d79598d8a5f83f79e7c7a5b5b5501b4ea0351c918c19fe446c"

    def test_frozen_hash_is_pinned(self):
        """study-1 and every published number were produced under exactly this config."""
        self.assertEqual(configs.load_config("frozen")["config_hash"], self.FROZEN_HASH,
                         "frozen config changed — published results no longer describe it")

    def test_replicate_seed42_is_the_frozen_config(self):
        self.assertEqual(configs.load_config("rep-s42")["config_hash"], self.FROZEN_HASH)


if __name__ == "__main__":
    unittest.main()
