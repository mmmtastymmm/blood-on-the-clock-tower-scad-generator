import os
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

# Import functions from the solid_maker module
from solid_maker import (
    convert_png_to_greyscale_png,
    get_relative_widths_pillow,
    felt_coin_model,
    role_overlay_model,
    download_png,
    convert_to_svg_with_potrace,
    export_coin_to_stl,
)


# Create a fixture for a temporary test image
@pytest.fixture
def test_image_path(tmp_path):
    """Create a simple test image for testing."""
    img_path = tmp_path / "test_image.png"
    # Create a simple 100x100 white image
    img = Image.new("RGBA", (100, 100), color=(255, 255, 255, 255))
    img.save(img_path)
    return img_path


def test_convert_png_to_greyscale_png(test_image_path, tmp_path):
    """Test that PNG to greyscale conversion works."""
    output_path = tmp_path / "greyscale.png"
    convert_png_to_greyscale_png(test_image_path, output_path)

    # Check that the output file exists
    assert os.path.exists(output_path)

    # Check that the output is a greyscale image
    img = Image.open(output_path)
    assert img.mode == "L"  # L is PIL's mode for greyscale


@patch("PIL.ImageFont.truetype")
def test_get_relative_widths_pillow(mock_truetype, tmp_path):
    """Test that relative widths calculation works correctly."""
    # Create a mock font
    mock_font = MagicMock()
    # Set up the getbbox method to return a bounding box with width 10 for each character
    mock_font.getbbox.return_value = (0, 0, 10, 20)  # x1, y1, x2, y2
    mock_truetype.return_value = mock_font

    # Test with a simple string
    test_string = "ABC"
    font_path = tmp_path / "test_font.ttf"

    # Create an empty file for the font path
    with open(font_path, 'w') as f:
        f.write('')

    widths = get_relative_widths_pillow(font_path, 12, test_string)

    # Check that we got the expected widths
    assert widths == {"A": 10, "B": 10, "C": 10}

    # Verify the font was loaded with the correct parameters
    mock_truetype.assert_called_once_with(font_path, 12)


def test_felt_coin_model():
    """Test that the felt coin model is created correctly."""
    # The felt_coin_model function returns a cylinder
    model = felt_coin_model()

    # We can't easily test the exact properties of the OpenSCAD model,
    # but we can verify it's not None and has the expected type
    assert model is not None

    # The model should be a cylinder object from the solid library
    assert "cylinder" in str(type(model))


@patch("solid_maker.import_")
@patch("solid_maker.translate")
@patch("solid_maker.linear_extrude")
@patch("solid_maker.text")
@patch("solid_maker.union")
@patch("solid_maker.get_relative_widths_pillow")
@patch("shutil.copy")
def test_role_overlay_model(mock_copy, mock_get_widths, mock_union, mock_text,
                            mock_extrude, mock_translate, mock_import):
    """Test that the role overlay model is created correctly."""
    # Set up mocks
    # Return a width for each character in "TEST ROLE" (uppercase)
    mock_get_widths.return_value = {
        "T": 10, "E": 10, "S": 10,
        "R": 10, "O": 10, "L": 10,
        " ": 14
    }
    mock_union.return_value = MagicMock()

    # Call the function
    result = role_overlay_model("Test Role", "test.svg")

    # Verify the SVG was copied
    mock_copy.assert_called_once_with("test.svg", "scads")

    # We can't easily test all the details, but we can verify the function ran without errors
    assert result is not None


@patch("requests.get")
def test_download_png(mock_get, tmp_path):
    """Test that PNG download works correctly."""
    # Set up mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"test content"
    mock_get.return_value = mock_response

    # Call the function
    output_path = tmp_path / "test_download.png"
    download_png("https://example.com/test.png", output_path)

    # Verify the request was made
    mock_get.assert_called_once_with("https://example.com/test.png")

    # Check that the file was created
    assert os.path.exists(output_path)

    # Check the file content
    with open(output_path, "rb") as f:
        assert f.read() == b"test content"


@patch("subprocess.run")
@patch("solid_maker.Path")
def test_convert_to_svg_with_potrace(mock_path, mock_run, test_image_path, tmp_path):
    """Test that PNG to SVG conversion works correctly."""
    # Set up mock subprocess.run to return success
    mock_run.return_value = MagicMock(returncode=0)

    # Convert Path objects to strings to avoid the Path.replace() issue
    png_path_str = str(test_image_path)
    output_path_str = str(tmp_path / "test_output.svg")

    # Call the function with string paths instead of Path objects
    convert_to_svg_with_potrace(png_path_str, output_path_str)

    # Verify subprocess.run was called twice (once for convert, once for potrace)
    assert mock_run.call_count == 2


@patch("subprocess.run")
def test_export_coin_to_stl(mock_run):
    """Test that SCAD to STL export works correctly."""
    # Set up mock subprocess.run to return success
    mock_run.return_value = MagicMock(returncode=0)

    # Call the function
    export_coin_to_stl("test_model", "test.scad", "test.stl")

    # Verify subprocess.run was called with the correct parameters
    mock_run.assert_called_once_with(
        ["openscad", "-o", "test.stl", "test.scad"],
        capture_output=True
    )
