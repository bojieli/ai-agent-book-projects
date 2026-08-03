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
