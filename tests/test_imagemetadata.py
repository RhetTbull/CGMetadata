"""Test ImageMetadata class"""

from __future__ import annotations

import pathlib
import shutil

import pytest

from cgmetadata import EXIF, GPS, IPTC, TIFF, XMP, ImageMetadata

TEST_HEIC = "tests/data/test.heic"
TEST_JPG = "tests/data/test.jpeg"
TEST_PNG = "tests/data/test.png"
TEST_RAW = "tests/data/test.cr2"
TEST_TIFF = "tests/data/test.tiff"

TEST_IMAGES_WRITEABLE = [TEST_JPG, TEST_PNG, TEST_HEIC, TEST_TIFF]
TEST_IMAGES = TEST_IMAGES_WRITEABLE + [TEST_RAW]

TEST_JPG_XMP = "tests/data/test.jpeg.xmp"
TEST_JPG_MODIFIED_XMP = "tests/data/modified.xmp"


def test_imagemetadata_asdict():
    """Test ImageMetadata().asdict()"""
    md = ImageMetadata(TEST_JPG)
    md_dict = md.asdict()
    assert md_dict.get(XMP, {}) == md.xmp
    assert md_dict.get(EXIF, {}) == md.exif
    assert md_dict.get(IPTC, {}) == md.iptc
    assert md_dict.get(TIFF, {}) == md.tiff
    assert md_dict.get(GPS, {}) == md.gps


def test_imagemetdata_xmp():
    """Test ImageMetadata().xmp"""
    md = ImageMetadata(TEST_JPG)
    assert sorted(md.xmp["dc:subject"]) == ["fruit", "tree"]


def test_imagemetadata_exif():
    """Test ImageMetadata().exif"""
    md = ImageMetadata(TEST_JPG)
    assert md.exif["LensMake"] == "Apple"


def test_imagemetadata_tiff():
    """Test ImageMetadata().tiff"""
    md = ImageMetadata(TEST_JPG)
    assert md.tiff["Make"] == "Apple"


def test_imagemetadata_iptc():
    """Test ImageMetadata().iptc"""
    md = ImageMetadata(TEST_JPG)
    assert md.iptc["Keywords"] == ["fruit", "tree"]


def test_imagemetadata_gps():
    """Test ImageMetadata().gps"""
    md = ImageMetadata(TEST_JPG)
    assert md.gps["LatitudeRef"] == "N"


@pytest.mark.parametrize("filepath", TEST_IMAGES)
def test_imagemetadata_filetypes(filepath: str):
    """Test ImageMetadata() with different filetypes"""
    md = ImageMetadata(filepath)
    assert md.xmp["dc:description"]


@pytest.mark.parametrize("filepath", TEST_IMAGES_WRITEABLE)
def test_imagemetadata_set_write_properties(filepath: str, tmp_path: pathlib.Path):
    """Test ImageMetadata().set, .write()"""

    # copy test image to temp directory
    test_file = tmp_path / pathlib.Path(filepath).name
    shutil.copy(filepath, test_file)

    md = ImageMetadata(test_file)
    assert md.exif.get("LensMake") != "modified"

    # ensure XMP and other properties are preserved
    # ensure properties are preserved
    make = md.tiff.get("Make")
    keywords = md.iptc.get("Keywords")
    latituderef = md.gps.get("LatitudeRef")
    description = md.xmp.get("dc:description")

    md.set(EXIF, "LensMake", "modified")
    md.write()
    assert md.exif["LensMake"] == "modified"
    assert md.xmp["exifEX:LensMake"] == "modified"

    # ensure XMP and other properties are preserved
    assert md.tiff.get("Make") == make
    assert md.iptc.get("Keywords") == keywords
    assert md.gps.get("LatitudeRef") == latituderef
    assert md.xmp.get("dc:description") == description


@pytest.mark.parametrize("filepath", TEST_IMAGES_WRITEABLE)
def test_imagemetadata_set_write_xmp_metadata(filepath: str, tmp_path: pathlib.Path):
    """Test ImageMetadata().set, .write() for XMP metadata"""

    # copy test image to temp directory
    test_file = tmp_path / pathlib.Path(filepath).name
    shutil.copy(filepath, tmp_path)

    md = ImageMetadata(test_file)
    assert md.xmp
    assert md.xmp.get("dc:creator") != ["modified"]

    # ensure properties are preserved
    lensmake = md.exif.get("LensMake")
    make = md.tiff.get("Make")
    keywords = md.iptc.get("Keywords")
    latituderef = md.gps.get("LatitudeRef")

    md.set(XMP, "dc:creator", "modified")
    md.write()

    assert md.xmp["dc:creator"] == ["modified"]
    assert md.exif.get("LensMake") == lensmake
    assert md.tiff.get("Make") == make
    assert md.iptc.get("Keywords") == keywords
    assert md.gps.get("LatitudeRef") == latituderef


def test_set_context_manager(tmp_path: pathlib.Path):
    """Test ImageMetadata().set() with context manager"""
    test_file = tmp_path / pathlib.Path(TEST_JPG).name
    shutil.copy(TEST_JPG, test_file)

    with ImageMetadata(test_file) as md:
        md.set(XMP, "dc:creator", "modified")
        md.set(EXIF, "LensMake", "modified")
        md.set(TIFF, "Make", "modified")

    md2 = ImageMetadata(test_file)
    assert md2.xmp["dc:creator"] == ["modified"]
    assert md2.exif["LensMake"] == "modified"
    assert md2.tiff["Make"] == "modified"


def test_xmp_dumps(tmp_path: pathlib.Path):
    """Test ImageMetadata().xmp_dumps()"""
    test_file = tmp_path / pathlib.Path(TEST_JPG).name
    shutil.copy(TEST_JPG, test_file)

    md = ImageMetadata(test_file)
    xmp = md.xmp_dumps()
    assert xmp.startswith("<?xpacket begin=") and xmp.endswith('<?xpacket end="w"?>')
    assert "dc:description" in xmp


def test_xmp_dumps_no_header(tmp_path: pathlib.Path):
    """Test ImageMetadata().xmp_dumps()"""
    test_file = tmp_path / pathlib.Path(TEST_JPG).name
    shutil.copy(TEST_JPG, test_file)

    md = ImageMetadata(test_file)
    xmp = md.xmp_dumps(header=False)
    assert "<?xpacket begin=" not in xmp and '<?xpacket end="w"?>' not in xmp
    assert "dc:description" in xmp


def test_xmp_dump(tmp_path: pathlib.Path):
    """Test ImageMetadata().xmp_dump()"""
    test_file = tmp_path / pathlib.Path(TEST_JPG).name
    shutil.copy(TEST_JPG, test_file)

    md = ImageMetadata(test_file)
    sidecar = tmp_path / "test.xmp"
    with open(sidecar, "w") as f:
        md.xmp_dump(f)
    xmp = sidecar.read_text()
    assert xmp.startswith("<?xpacket begin=") and xmp.endswith('<?xpacket end="w"?>')
    assert "dc:description" in xmp


def test_xmp_dump_no_header(tmp_path: pathlib.Path):
    """Test ImageMetadata().xmp_dump()"""
    test_file = tmp_path / pathlib.Path(TEST_JPG).name
    shutil.copy(TEST_JPG, test_file)

    md = ImageMetadata(test_file)
    sidecar = tmp_path / "test.xmp"
    with open(sidecar, "w") as f:
        md.xmp_dump(f, header=False)
    xmp = sidecar.read_text()
    assert "<?xpacket begin=" not in xmp and '<?xpacket end="w"?>' not in xmp
    assert "dc:description" in xmp


def test_xmp_loads(tmp_path: pathlib.Path):
    """Test ImageMetadata().xmp_loads()"""
    test_file = tmp_path / pathlib.Path(TEST_JPG).name
    shutil.copy(TEST_JPG, test_file)

    md = ImageMetadata(test_file)
    assert not sorted(md.xmp["dc:subject"]) == ["Bar", "Foo"]
    md.xmp_loads(pathlib.Path(TEST_JPG_MODIFIED_XMP).read_text())
    md.write()
    assert md.xmp["dc:creator"] == ["modified"]
    assert sorted(md.xmp["dc:subject"]) == ["Bar", "Foo"]


def test_xmp_load(tmp_path: pathlib.Path):
    """Test ImageMetadata().xmp_load()"""
    test_file = tmp_path / pathlib.Path(TEST_JPG).name
    shutil.copy(TEST_JPG, test_file)

    md = ImageMetadata(test_file)
    assert not sorted(md.xmp["dc:subject"]) == ["Bar", "Foo"]
    with open(TEST_JPG_MODIFIED_XMP) as f:
        md.xmp_load(f)
    md.write()
    assert md.xmp["dc:creator"] == ["modified"]
    assert sorted(md.xmp["dc:subject"]) == ["Bar", "Foo"]
