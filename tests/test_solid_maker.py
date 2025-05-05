import os
import pytest
from pathlib import Path
from PIL import Image

# Import functions from the solid_maker module
from solid_maker import (
    calculate_scale_factor,
    convert_png_to_greyscale_png,
    create_silhouette_image
)

# Create a fixture for a temporary test image
@pytest.fixture
def test_image_path(tmp_path):
    """Create a simple test image for testing."""
    img_path = tmp_path / "test_image.png"
    # Create a simple 100x100 white image
    img = Image.new('RGBA', (100, 100), color=(255, 255, 255, 255))
    img.save(img_path)
    return img_path

def test_calculate_scale_factor(test_image_path):
    """Test that the scale factor calculation works correctly."""
    # For a 100x100 image and a diameter of 50, the scale factor should be 0.35
    # (70% of 50 = 35, divided by 100 = 0.35)
    scale_factor = calculate_scale_factor(test_image_path, 50)
    assert scale_factor == pytest.approx(0.35, abs=0.01)

def test_convert_png_to_greyscale_png(test_image_path, tmp_path):
    """Test that PNG to greyscale conversion works."""
    output_path = tmp_path / "greyscale.png"
    convert_png_to_greyscale_png(test_image_path, output_path)
    
    # Check that the output file exists
    assert os.path.exists(output_path)
    
    # Check that the output is a greyscale image
    img = Image.open(output_path)
    assert img.mode == "L"  # L is PIL's mode for greyscale

def test_create_silhouette_image(test_image_path, tmp_path):
    """Test that silhouette image creation works."""
    output_path = tmp_path / "silhouette.png"
    create_silhouette_image(test_image_path, output_path)
    
    # Check that the output file exists
    assert os.path.exists(output_path)
    
    # Check that the output is a black and white image
    img = Image.open(output_path)
    assert img.mode == "1"  # 1 is PIL's mode for 1-bit black and white