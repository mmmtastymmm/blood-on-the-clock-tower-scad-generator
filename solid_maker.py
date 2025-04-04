import os
import json
import shutil

import requests
from solid import *
from solid.utils import *
from solid import scad_render_to_file
from PIL import Image


def calculate_scale_factor(greyscale_image, diameter: float) -> float:
    """
    Opens the provided greyscale image and calculates a scale factor so that the image
    will occupy 55% of the coin's diameter in its largest dimension.
    """
    img = Image.open(greyscale_image)
    width, height = img.size
    desired_diameter = diameter * 0.55
    scale_factor = desired_diameter / max(width, height)
    return scale_factor


def coin_model(role_name, greyscale_png_filename,
               diameter=50, height=6,
               text_depth=2, text_size=3,
               desired_relief_height=6.0):
    """
    Creates a coin model with an engraved relief (image) on the coin’s top.
    The relief is normalized so that the minimum pixel value in the image becomes 0
    and the maximum pixel value corresponds to a height of `desired_relief_height` in mm.
    """
    # Convert the image file path to an absolute path with forward slashes.
    abs_path = Path(os.path.abspath(greyscale_png_filename).replace('\\', '/'))
    shutil.copy(greyscale_png_filename, "scads")
    print(
        f"Copied {greyscale_png_filename} to scads directory for use in OpenSCAD."
    )

    # Create the base coin as a simple cylinder.
    coin = cylinder(d=diameter, h=height)

    # Calculate the XY scale factor so the image fits nicely on the coin.
    scale_factor = calculate_scale_factor(greyscale_png_filename, diameter)

    # Open the image to get the pixel value range.
    # This will be used to normalize the relief height.
    from PIL import Image
    img = Image.open(greyscale_png_filename)
    min_pixel, max_pixel = img.getextrema()  # Example: (47, 255)

    # Compute a z-scale so that the pixel range maps to the desired relief height.
    z_scale = desired_relief_height / (max_pixel - min_pixel)

    # Create the image relief using SolidPython's surface() function.
    # The 'center=True' option centers the relief geometry.
    image_relief = surface(file=abs_path.stem + abs_path.suffix, center=True)
    # Scale the relief in the XY dimensions by the calculated factor and in the Z dimension by z_scale.
    image_relief = scale((scale_factor, scale_factor, z_scale))(image_relief)

    # Translate the relief upward so that its base (corresponding to the minimum pixel value)
    # aligns with the top of the coin (z = height).
    image_relief = translate((0, 0, height - min_pixel * z_scale))(image_relief)

    # (Optional) Color the relief for debugging; uncomment if needed.
    # image_relief = color("red")(image_relief)

    # Create the engraved text by extruding the role name.
    engraved_text = linear_extrude(height=text_depth)(
        text(role_name, size=text_size, halign="center", valign="center")
    )
    # Position the text so that it is engraved on the lower half of the coin's front.
    engraved_text = translate((0, -diameter / 2 + text_size + 5, height - text_depth / 2))(engraved_text)

    # Subtract both the engraved text and the image relief from the base coin,
    # resulting in an engraved coin.
    final_coin = coin - engraved_text - image_relief
    return final_coin


def download_png(url, filename):
    """
    Downloads a PNG image from the provided URL and saves it to 'filename'.
    """
    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"Downloaded {filename}")
    else:
        raise Exception(f"Failed to download {url}")


def convert_png_to_greyscale_png(png_path, greyscale_png_path):
    """
    Converts a PNG image to a greyscale version.
    The conversion composites the PNG on a white background (removing transparency)
    and then converts it to greyscale before saving.
    """
    img = Image.open(png_path).convert("RGBA")
    background = Image.new("RGBA", img.size, (255, 255, 255))
    composite = Image.alpha_composite(background, img)
    greyscale_img = composite.convert("L")
    greyscale_img.save(greyscale_png_path)
    print(f"Converted {png_path} to {greyscale_png_path}")


def main():
    # Load the role data from 'roles.json'.
    with open("roles.json") as f:
        roles = json.load(f)

    # Create output directories for PNGs, greyscale PNGs, and SCAD files if they do not already exist.
    os.makedirs("pngs", exist_ok=True)
    os.makedirs("grey_pngs", exist_ok=True)
    os.makedirs("scads", exist_ok=True)

    # Iterate over each role in the JSON map.
    count = 0
    for role, data in roles.items():
        # Create a safe filename by replacing spaces and apostrophes.
        role_safe = role.replace(" ", "_").replace("'", "")
        png_filename = os.path.join("pngs", f"{role_safe}.png")
        grey_png_filename = os.path.join("grey_pngs", f"{role_safe}.png")
        scad_filename = os.path.join("scads", f"{role_safe}_coin.scad")

        # Download the PNG image if it does not already exist.
        if not os.path.exists(png_filename):
            download_png(data["image"], png_filename)

        # Convert the downloaded PNG image to a greyscale image.
        convert_png_to_greyscale_png(png_filename, grey_png_filename)

        # Generate the coin model using the greyscale image.
        model = coin_model(role, grey_png_filename)

        # Render the coin model to an OpenSCAD (.scad) file.
        scad_render_to_file(model, scad_filename, file_header='$fn=100;')
        print(f"Generated {scad_filename} for role {role}")


if __name__ == "__main__":
    main()
