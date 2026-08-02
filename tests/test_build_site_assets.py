from pathlib import Path
import subprocess


def run_cleanup(site: Path) -> None:
    helper = Path(__file__).parents[1] / "scripts" / "clean_site_files.py"
    subprocess.run(["python3", str(helper), str(site)], check=True)


def test_cleanup_preserves_rendered_json_links_only(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    linked = site / "evidence.json"
    referenced = site / "reference.json"
    root_linked = site / "root.json"
    orphan = site / "raw-results.json"
    code_example = site / "secret.json"
    source = site / "experiment.py"
    (site / "nested").mkdir()
    (site / "nested" / "README.md").write_text(
        """[evidence](../evidence%2Ejson?download=1#receipt)
[root](/root.json)
[reference][run]
[run]: ../reference.json

`[not a link](../secret.json)`

```md
This example deliberately contains a blank line because Python-Markdown can
otherwise interpret the entire fence as one multiline inline-code span.

[not a link](../secret.json)
```
"""
    )
    for path in [linked, referenced, root_linked, orphan, code_example]:
        path.write_text('{"status": "complete"}\n')
    source.write_text("print('not a site asset')\n")

    run_cleanup(site)

    assert linked.exists()
    assert referenced.exists()
    assert root_linked.exists()
    assert not orphan.exists()
    assert not code_example.exists()
    assert not source.exists()


def test_cleanup_rejects_external_links_and_escaping_symlinks(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"secret": true}\n')
    (site / "README.md").write_text(
        "[external](https://example.com/evidence.json)\n"
        "[escape](../outside.json)\n"
        "[symlink](escape.json)\n"
    )
    (site / "escape.json").symlink_to(outside)
    (site / "escape.md").symlink_to(tmp_path / "missing.md")

    run_cleanup(site)

    assert outside.exists()
    assert not (site / "escape.json").exists()
    assert not (site / "escape.md").exists()
