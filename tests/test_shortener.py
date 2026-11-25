"""단축기 테스트. 실행: make test"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from probing_table import ProbingHashTable  # noqa: E402
from shortener import Shortener  # noqa: E402


class TestShortener(unittest.TestCase):
    def setUp(self):
        self.s = Shortener()

    def test_first_code_is_1(self):
        self.assertEqual(self.s.shorten("https://www.yonsei.ac.kr"), "1")

    def test_code_sequence_boundaries(self):
        codes = [self.s.shorten(f"https://example.com/{i}") for i in range(63)]
        self.assertEqual(codes[0], "1")   # 1번째 URL -> encode(1)
        self.assertEqual(codes[1], "2")   # 2번째 URL -> encode(2)
        self.assertEqual(codes[60], "Z")  # 61번째 URL -> encode(61)
        self.assertEqual(codes[61], "10") # 62번째 URL -> encode(62)
        self.assertEqual(codes[62], "11") # 63번째 URL -> encode(63)

    def test_round_trip(self):
        urls = [f"https://example.com/{i}" for i in range(200)]
        codes = [self.s.shorten(u) for u in urls]
        self.assertEqual(len(set(codes)), 200)
        for u, c in zip(urls, codes):
            self.assertEqual(self.s.expand(c), u)

    def test_same_url_same_code(self):
        a = self.s.shorten("https://a.com")
        b = self.s.shorten("https://a.com")
        c = self.s.shorten("https://b.com")
        self.assertEqual(a, b)
        self.assertEqual(c, "2")  # 번호를 하나만 썼다

    def test_strip_spaces(self):
        a = self.s.shorten("https://a.com")
        self.assertEqual(self.s.shorten("  https://a.com\n"), a)
        self.assertEqual(self.s.expand(a), "https://a.com")

    def test_invalid_urls(self):
        for bad in ["ftp://a.com", "www.a.com", "http://", "https://a b",
                    "https://a\tb", "https://a\nb",
                    "https://example.com/한글",
                    "https://" + "a" * 2041, ""]:
            with self.assertRaises(ValueError, msg=bad):
                self.s.shorten(bad)

    def test_long_url_limit(self):
        ok = "https://" + "a" * 2040  # 정확히 2048자
        self.assertEqual(len(ok), 2048)
        self.assertEqual(self.s.expand(self.s.shorten(ok)), ok)

    def test_unknown_code(self):
        self.s.shorten("https://a.com")
        self.assertIsNone(self.s.expand("zzz"))
        self.assertIsNone(self.s.expand("!!"))
        self.assertIsNone(self.s.expand(""))


class TestShortenerWithProbing(TestShortener):
    """같은 테스트를 선형 탐지 테이블로 한 번 더 돌린다."""

    def setUp(self):
        self.s = Shortener(table=ProbingHashTable)


if __name__ == "__main__":
    unittest.main()
