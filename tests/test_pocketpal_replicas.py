"""Golden tests for the functions that replicate PocketPal PR #808 behaviour.

These exist because the harness's whole claim is "this is what the app does". If one of
these drifts, every published number silently stops describing PocketPal. Values below are
pinned to the current implementation; changing one means either a deliberate contract change
(update CONTRACT.md in the same commit) or a bug.
"""
import unittest

from _harness_path import common  # noqa: E402


class TestEstimateTokens(unittest.TestCase):
    def test_ceil_div_four(self):
        self.assertEqual(common.estimate_tokens(""), 0)
        self.assertEqual(common.estimate_tokens("a"), 1)      # ceil(1/4)
        self.assertEqual(common.estimate_tokens("abcd"), 1)
        self.assertEqual(common.estimate_tokens("abcde"), 2)  # ceil(5/4)
        self.assertEqual(common.estimate_tokens("x" * 280), 70)


class TestToPlainText(unittest.TestCase):
    def test_strips_html_tags(self):
        self.assertEqual(common.to_plain_text("<b>bold</b> text"), "bold text")

    def test_markdown_link_keeps_label_drops_url(self):
        self.assertEqual(common.to_plain_text("see [the docs](https://x.com/a)"), "see the docs")

    def test_markdown_image_removed_entirely(self):
        self.assertEqual(common.to_plain_text("a ![alt](http://i.png) b"), "a b")

    def test_image_stripped_before_link_rule(self):
        # ordering matters: if the link rule ran first, "!alt" would survive
        self.assertEqual(common.to_plain_text("![alt](u)"), "")

    def test_emphasis_chars_removed(self):
        self.assertEqual(common.to_plain_text("**a** _b_ `c` #d >e ~f"), "a b c d e f")

    def test_whitespace_collapsed_and_trimmed(self):
        self.assertEqual(common.to_plain_text("  a\n\n\tb   c  "), "a b c")

    def test_none_is_safe(self):
        self.assertEqual(common.to_plain_text(None), "")


class TestTruncateOnWordBoundary(unittest.TestCase):
    def test_under_limit_is_untouched_and_gets_no_ellipsis(self):
        self.assertEqual(common.truncate_on_word_boundary("hello", 10), "hello")

    def test_exactly_at_limit_is_untouched(self):
        self.assertEqual(common.truncate_on_word_boundary("hello", 5), "hello")

    def test_cuts_on_word_boundary(self):
        self.assertEqual(common.truncate_on_word_boundary("alpha beta gamma", 12), "alpha beta…")

    def test_hard_cut_when_boundary_too_early(self):
        # no space past max_chars//2 -> hard char cut rather than losing most of the text
        self.assertEqual(common.truncate_on_word_boundary("a bbbbbbbbbbbbbbbb", 10), "a bbbbbbbb…")

    def test_result_never_exceeds_limit_plus_ellipsis(self):
        for n in range(1, 40):
            out = common.truncate_on_word_boundary("the quick brown fox jumps over it", n)
            self.assertLessEqual(len(out.rstrip("…")), n)


if __name__ == "__main__":
    unittest.main()
