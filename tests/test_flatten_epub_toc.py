import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flatten_epub_toc import flatten_nav, flatten_ncx


def test_flatten_nav_after_flatten_ncx_preserves_default_xhtml_namespace():
    """Contract: flatten_nav must re-register the default XHTML namespace so that element serialization
    does not emit unwanted 'ns0:' namespace prefixes even if flatten_ncx was called previously.
    """
    nav_xml = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>TOC</title></head>
<body>
<nav epub:type="toc">
  <ol>
    <li><a href="ch1.xhtml"><span class="section-header-number">1</span> Chapter 1</a></li>
  </ol>
</nav>
</body>
</html>"""

    ncx_xml = """<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <navMap>
    <navPoint id="navPoint-1" playOrder="1">
      <navLabel><text>1 Chapter 1</text></navLabel>
      <content src="ch1.xhtml"/>
    </navPoint>
  </navMap>
</ncx>"""

    # Call flatten_ncx first, which registers default NCX namespace
    flatten_ncx(ncx_xml, "Title", "TOC")

    # Calling flatten_nav afterwards should still output clean XHTML without ns0: prefix
    result = flatten_nav(nav_xml, "Title", "TOC").decode("utf-8")
    assert "<ns0:html" not in result
    assert "<html" in result
    assert 'xmlns="http://www.w3.org/1999/xhtml"' in result


def test_flatten_nav_does_not_add_chapter_group_class_to_inserted_title_and_contents():
    """Contract: flatten_nav must insert title-page and contents TOC items after iterating over
    chapter items, so that top-level non-chapter entries are not tagged with class 'chapter-group'.
    """
    nav_xml = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>TOC</title></head>
<body>
<nav epub:type="toc">
  <ol>
    <li><a href="ch1.xhtml">Chapter 1</a></li>
  </ol>
</nav>
</body>
</html>"""

    result = flatten_nav(nav_xml, "Title Page", "Contents").decode("utf-8")
    assert 'id="toc-li-title-page" class="chapter-group"' not in result
    assert 'id="toc-li-contents" class="chapter-group"' not in result

def test_flatten_ncx_after_flatten_nav_preserves_default_ncx_namespace():
    """Contract: flatten_ncx must output default NCX namespace without ns0: prefix even if flatten_nav ran first."""
    nav_xml = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>TOC</title></head>
<body><nav epub:type="toc"><ol><li><a href="ch1.xhtml">Ch 1</a></li></ol></nav></body>
</html>"""

    ncx_xml = """<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <navMap>
    <navPoint id="navPoint-1" playOrder="1">
      <navLabel><text>1 Chapter 1</text></navLabel>
      <content src="ch1.xhtml"/>
    </navPoint>
  </navMap>
</ncx>"""

    # Run nav first, then ncx
    flatten_nav(nav_xml, "Title", "TOC")
    result = flatten_ncx(ncx_xml, "Title", "TOC").decode("utf-8")
    assert "<ns0:ncx" not in result
    assert "<ncx" in result
    assert 'xmlns="http://www.daisy.org/z3986/2005/ncx/"' in result


def test_flatten_nav_inserted_top_level_nav_items_order_and_attributes():
    """Contract: inserted top-level nav items (title-page, contents) are placed first in order
    and preserve XHTML element tag without chapter-group class.
    """
    nav_xml = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>TOC</title></head>
<body>
<nav epub:type="toc">
  <ol>
    <li><a href="ch1.xhtml">Chapter 1</a></li>
  </ol>
</nav>
</body>
</html>"""

    result = flatten_nav(nav_xml, "Title Page", "Contents").decode("utf-8")
    title_pos = result.find('id="toc-li-title-page"')
    contents_pos = result.find('id="toc-li-contents"')
    ch1_pos = result.find('href="ch1.xhtml"')

    assert title_pos != -1
    assert contents_pos != -1
    assert ch1_pos != -1
    assert title_pos < contents_pos < ch1_pos
    assert 'class="chapter-group"' in result[ch1_pos - 100 : ch1_pos + 100]
