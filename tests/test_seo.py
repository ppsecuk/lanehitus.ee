"""Validate generated search metadata without requesting the hosted site."""
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = 'https://lanehitus.ee/'
LANGUAGES = {'et': ('et-EE', 'et_EE', ''), 'ru': ('ru-EE', 'ru_EE', 'ru/')}
SERVICE_IDS = {'terraces', 'drywall', 'flooring', 'doors', 'furniture'}


class Page(HTMLParser):
    """Keep semantic elements and script data while ignoring executable scripts."""

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.ids = set()
        self.titles = []
        self.headings = []
        self.prose = []
        self.json_scripts = []
        self._capture = None
        self._text = []
        self._script_type = None
        self._script = []
        self._skip = 0
        self._language = None
        self._stack = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self._language = attrs.get('lang')
        inherited_language = self._stack[-1][1] if self._stack else self._language
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                       'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self._stack.append((tag, attrs.get('lang', inherited_language)))
        self.tags.append((tag, attrs))
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'script':
            self._script_type = attrs.get('type', '')
            self._script = []
            self._skip += 1
        elif tag == 'style':
            self._skip += 1
        elif tag in ('title', 'h1'):
            self._capture = tag
            self._text = []

    def handle_endtag(self, tag):
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                del self._stack[index:]
                break
        if tag == 'script':
            if self._script_type == 'application/ld+json':
                self.json_scripts.append(json.loads(''.join(self._script)))
            self._script_type = None
            self._skip -= 1
        elif tag == 'style':
            self._skip -= 1
        elif tag == self._capture:
            text = ''.join(self._text).strip()
            (self.titles if tag == 'title' else self.headings).append(text)
            self._capture = None

    def handle_data(self, data):
        if self._script_type is not None:
            self._script.append(data)
        elif not self._skip:
            active_language = self._stack[-1][1] if self._stack else self._language
            if active_language == self._language:
                self.prose.append(data)
            if self._capture:
                self._text.append(data)

    def elements(self, tag, **attrs):
        return [item for name, item in self.tags
                if name == tag and all(item.get(key) == value for key, value in attrs.items())]

    def metadata(self, name, *, property=False):
        key = 'property' if property else 'name'
        return [attrs.get('content') for attrs in self.elements('meta', **{key: name})]


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def media_blocks(css):
    """Read balanced media blocks so a rule cannot pass from another breakpoint."""
    for match in re.finditer(r'@media\b([^{}]*)\{', css):
        depth = 1
        end = match.end()
        while end < len(css) and depth:
            depth += (css[end] == '{') - (css[end] == '}')
            end += 1
        yield match.group(1), css[match.end():end - 1]


class MetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('lan_seo_test', ROOT / 'website' / 'seo.py')
        cls.seo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.seo)

    def assert_metadata(self, page, language, title, description, *, ids=None):
        region, locale, path = LANGUAGES[language]
        canonical = BASE_URL + path
        self.assertEqual(page.elements('link', rel='canonical'),
                         [{'rel': 'canonical', 'href': canonical}])
        alternates = page.elements('link', rel='alternate')
        expected = {'et-EE': BASE_URL, 'ru-EE': BASE_URL + 'ru/', 'x-default': BASE_URL}
        self.assertEqual(len(alternates), len(expected))
        self.assertEqual({link.get('hreflang'): link.get('href') for link in alternates}, expected)
        self.assertEqual(page.metadata('og:title', property=True), [title])
        self.assertEqual(page.metadata('og:description', property=True), [description])
        self.assertEqual(page.metadata('og:url', property=True), [canonical])
        self.assertEqual(page.metadata('og:locale', property=True), [locale])
        self.assertEqual(page.metadata('og:locale:alternate', property=True),
                         [LANGUAGES['ru' if language == 'et' else 'et'][1]])
        image, = page.metadata('og:image', property=True)
        image_url = urlsplit(image)
        self.assertEqual(image_url.scheme, 'https')
        self.assertEqual(image_url.netloc, 'lanehitus.ee')
        self.assertTrue((ROOT / image_url.path.lstrip('/')).is_file(), image)
        self.assertFalse(image_url.fragment)
        robots, = page.metadata('robots')
        directives = {part.strip().lower() for part in robots.split(',')}
        self.assertTrue({'index', 'follow', 'max-image-preview:large'} <= directives)

        document, = page.json_scripts
        self.assertEqual(document.get('@context'), 'https://schema.org')
        graph = document['@graph']
        organizations = [node for node in graph if node.get('@type') == 'Organization']
        websites = [node for node in graph if node.get('@type') == 'WebSite']
        webpages = [node for node in graph if node.get('@type') == 'WebPage']
        services = [node for node in graph if node.get('@type') == 'Service']
        self.assertEqual(len(organizations), 1)
        self.assertEqual(len(websites), 1)
        self.assertEqual(len(webpages), 1)
        self.assertEqual(len(services), 5)
        organization, website, webpage = organizations[0], websites[0], webpages[0]
        self.assertEqual(organization['@id'], BASE_URL + '#organization')
        self.assertEqual(organization['name'], 'LAN OÜ')
        self.assertEqual(website['@id'], BASE_URL + '#website')
        self.assertEqual(set(website['inLanguage']), {item[0] for item in LANGUAGES.values()})
        self.assertEqual(webpage['@id'], canonical + '#webpage')
        self.assertEqual(webpage['url'], canonical)
        self.assertEqual(webpage['name'], title)
        self.assertEqual(webpage['description'], description)
        self.assertEqual(webpage['inLanguage'], region)
        self.assertEqual(webpage['isPartOf']['@id'], website['@id'])
        self.assertEqual({service['@id'] for service in services},
                         {canonical + '#' + slug for slug in SERVICE_IDS})
        self.assertEqual({item['@id'] for item in webpage['mainEntity']},
                         {service['@id'] for service in services})
        for service in services:
            self.assertEqual(service['provider']['@id'], organization['@id'])
            self.assertEqual(service['url'], service['@id'])
            area = service['areaServed']
            if not isinstance(area, list):
                area = [area]
            self.assertEqual({place['name'] for place in area}, {'Tallinn', 'Harjumaa'})
            self.assertTrue(all(place['@type'] in ('City', 'AdministrativeArea') for place in area))
            for place in area:
                self.assertEqual(place['containedInPlace']['@type'], 'Country')
                self.assertEqual(place['containedInPlace']['identifier'], 'EE')
            if ids is not None:
                self.assertIn(urlsplit(service['url']).fragment, ids)
        forbidden = {'address', 'openingHours', 'openingHoursSpecification', 'aggregateRating',
                     'review', 'sameAs', 'telephone', 'email', 'contactPoint', 'faxNumber'}
        for node in walk(document):
            self.assertFalse(forbidden.intersection(node), forbidden.intersection(node))

    def test_head_metadata_for_both_languages(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                title, description = 'LAN OÜ – Tallinn & Harjumaa', 'Work for your home.'
                self.assert_metadata(Page(self.seo.render_metadata(language, title, description)),
                                     language, title, description)

    def test_html_and_json_escape_untrusted_copy_without_changing_values(self):
        title = 'LAN OÜ "quote" & <tag> </title><script>alert("title")</script>'
        description = 'Text \" & < > </script><script>alert("description")</script> Õ Ё \u2028'
        for language in LANGUAGES:
            with self.subTest(language=language):
                output = self.seo.render_metadata(language, title, description)
                page = Page(output)
                self.assert_metadata(page, language, title, description)
                scripts = page.elements('script')
                self.assertEqual(len(scripts), 1)
                self.assertEqual(scripts[0].get('type'), 'application/ld+json')
                self.assertFalse(page.elements('tag'))

    def test_unsupported_language_is_rejected(self):
        with self.assertRaises(ValueError):
            self.seo.render_metadata('en', 'Title', 'Description')

    def test_crawler_files_have_only_canonical_public_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.seo.write_crawler_files(root)
            for filename in ('robots.txt', 'sitemap.xml'):
                self.assertEqual((ROOT / filename).read_text(), (root / filename).read_text(),
                                 filename + ' must be included in the generated site.')
            sitemap = ET.parse(root / 'sitemap.xml').getroot()
            namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
            self.assertEqual(sitemap.tag, namespace + 'urlset')
            urls = sitemap.findall(namespace + 'url')
            self.assertEqual(len(urls), 2)
            self.assertEqual({node.findtext(namespace + 'loc') for node in urls},
                             {BASE_URL, BASE_URL + 'ru/'})
            self.assertFalse(sitemap.findall('.//' + namespace + 'lastmod'))
            for node in urls:
                url = urlsplit(node.findtext(namespace + 'loc'))
                self.assertFalse(url.query or url.fragment)
            lines = (root / 'robots.txt').read_text().splitlines()
            self.assertIn('User-agent: *', lines)
            self.assertIn('Allow: /', lines)
            self.assertIn('Sitemap: ' + BASE_URL + 'sitemap.xml', lines)
            self.assertNotIn('Disallow: /', lines)

    def test_generated_pages_are_localized_and_retain_performance_changes(self):
        for language, (_, _, path) in LANGUAGES.items():
            with self.subTest(language=language):
                page = Page((ROOT / path / 'index.html').read_text())
                self.assertEqual(page.elements('html')[0].get('lang'), language)
                title, = page.titles
                description, = page.metadata('description')
                heading, = page.headings
                self.assertRegex(title, r'\bLAN\b')
                for value in (title, description, heading):
                    self.assertRegex(value.lower(), r'tallinn|таллин')
                    self.assertRegex(value.lower(), r'harju|харью')
                self.assert_metadata(page, language, title, description, ids=page.ids)
                if language == 'et':
                    self.assertNotRegex(' '.join(page.prose), r'[\u0400-\u04ff]')
                slides = [attrs for tag, attrs in page.tags if tag == 'img'
                          and 'carousel-slide' in attrs.get('class', '').split()]
                self.assertTrue(slides)
                self.assertTrue(all('data-fullsrc' in image for image in slides))
                self.assertTrue(any('src' not in image and 'data-srcset' in image for image in slides))
                self.assertTrue(all('/images/optimized/' in image['src'] for image in slides if 'src' in image))
                css, = page.elements('link', rel='stylesheet')
                self.assertTrue(parse_qs(urlsplit(css['href']).query).get('v'))
                scripts = [attrs['src'] for attrs in page.elements('script') if 'src' in attrs]
                self.assertTrue(any(urlsplit(src).path == '/website.js'
                                    and parse_qs(urlsplit(src).query).get('v') for src in scripts))
        css = (ROOT / 'website.css').read_text()
        self.assertTrue(any(
            re.search(r'max-width\s*:\s*700px', query)
            and re.search(r'\.price-table tbody td:nth-child\(2\) strong\s*\{[^}]*font-size\s*:\s*28px', body)
            for query, body in media_blocks(css)
        ), 'Mobile price numbers must retain their 28px rule.')

    def test_legacy_redirect_pages_do_not_compete_with_the_homepage(self):
        legacy_pages = [path for path in ROOT.rglob('index.html')
                        if path not in (ROOT / 'index.html', ROOT / 'ru' / 'index.html')]
        self.assertTrue(legacy_pages)
        for path in legacy_pages:
            with self.subTest(path=str(path.relative_to(ROOT))):
                page = Page(path.read_text())
                self.assertEqual(page.elements('link', rel='canonical'),
                                 [{'rel': 'canonical', 'href': BASE_URL}])
                robots, = page.metadata('robots')
                self.assertIn('noindex', {part.strip().lower() for part in robots.split(',')})


if __name__ == '__main__':
    unittest.main()
