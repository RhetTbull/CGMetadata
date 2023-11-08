"""Test CLI command """

from __future__ import annotations

import json

import pytest

from cgmetadata import __version__
from cgmetadata.cli import main

TEST_JPG = "tests/data/test.jpeg"


@pytest.mark.parametrize("arg", ["--version", "-v"])
def test_version(arg, capsys, monkeypatch):
    """Test --verpsion option"""
    monkeypatch.setattr("sys.argv", ["cgmd", arg])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert f"{__version__}" in captured.out


@pytest.mark.parametrize("arg", ["--help", "-h"])
def test_help(arg, capsys, monkeypatch):
    """Test --help"""
    monkeypatch.setattr("sys.argv", ["cgmd", arg])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "usage:" in captured.out


@pytest.mark.parametrize("arg", ["--csv", "-c"])
def test_csv_output(arg, capsys, monkeypatch):
    """Test --csv output"""
    monkeypatch.setattr("sys.argv", ["cgmd", arg, TEST_JPG])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "Group,Tag,Value" in captured.out
    assert "dc:subject" in captured.out


@pytest.mark.parametrize("arg", ["--no-header", "-H"])
def test_csv_output_no_header(arg, capsys, monkeypatch):
    """Test --csv output with --no-header"""
    monkeypatch.setattr("sys.argv", ["cgmd", "--csv", arg, TEST_JPG])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "Group,Tag,Value" not in captured.out
    assert "dc:subject" in captured.out


@pytest.mark.parametrize("arg", ["--tsv", "-t"])
def test_tsv_output(arg, capsys, monkeypatch):
    """Test --tsv output"""
    monkeypatch.setattr("sys.argv", ["cgmd", arg, TEST_JPG])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "Group\tTag\tValue" in captured.out
    assert "dc:subject" in captured.out


@pytest.mark.parametrize("arg", ["--no-header", "-H"])
def test_tsv_output_no_header(arg, capsys, monkeypatch):
    """Test --tsv output with --no-header"""
    monkeypatch.setattr("sys.argv", ["cgmd", "--tsv", arg, TEST_JPG])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "Group\tTag\tValue" not in captured.out
    assert "dc:subject" in captured.out


@pytest.mark.parametrize("arg", ["--json", "-j"])
def test_json_output(arg, capsys, monkeypatch):
    """Test --json output"""
    monkeypatch.setattr("sys.argv", ["cgmd", arg, TEST_JPG])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["XMP"]["dc:subject"] == ["fruit", "tree"]


@pytest.mark.parametrize("arg", ["--indent", "-i"])
def test_json_indent(arg, capsys, monkeypatch):
    """Test --json output with --indent"""
    monkeypatch.setattr("sys.argv", ["cgmd", "--json", arg, "2", TEST_JPG])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["XMP"]["dc:subject"] == ["fruit", "tree"]


def test_table_output(capsys, monkeypatch):
    """Test table output"""
    monkeypatch.setattr("sys.argv", ["cgmd", TEST_JPG])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "Group" in captured.out
    assert "dc:subject" in captured.out
    assert "fruit, tree" in captured.out


@pytest.mark.parametrize("arg", ["--xmp", "-x"])
def test_xmp_output(arg, capsys, monkeypatch):
    """Test --xmp output"""
    monkeypatch.setattr("sys.argv", ["cgmd", arg, TEST_JPG])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert '<x:xmpmeta xmlns:x="adobe:ns:meta/"' in captured.out
    assert "dc:subject" in captured.out
    # test packet header
    assert 'id="W5M0MpCehiHzreSzNTczkc9d"?>' in captured.out


@pytest.mark.parametrize("arg", ["--no-header", "-H"])
def test_xmp_output_no_header(arg, capsys, monkeypatch):
    """Test --xmp output with --no-header"""
    monkeypatch.setattr("sys.argv", ["cgmd", "--xmp", arg, TEST_JPG])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert '<x:xmpmeta xmlns:x="adobe:ns:meta/"' in captured.out
    assert "dc:subject" in captured.out
    # test packet header
    assert 'id="W5M0MpCehiHzreSzNTczkc9d"?>' not in captured.out
