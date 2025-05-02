import os
import json
import shutil
import subprocess
import textwrap
import math

import requests
from solid import *
from solid.utils import *
from solid import scad_render_to_file
from PIL import Image, ImageOps


def calculate_scale_factor(greyscale_image, diameter: float) -> float:
    """
    Opens the provided greyscale image and calculates a scale factor so that the image
    will occupy 55% of the coin's diameter in its largest dimension.
    """
    img = Image.open(greyscale_image)
    width, height = img.size
    desired_diameter = diameter * 0.70
    scale_factor = desired_diameter / max(width, height)
    return scale_factor


def base_coin_model(diameter=50, height=6,
                    bottom_hatch_width=1, bottom_hatch_spacing=3, bottom_hatch_depth=1,
                    edge_hatch_width=3, edge_hatch_spacing=10, edge_hatch_depth=1):
    """
    Creates a base coin with a hatch pattern cut into the bottom and the side edges.

    Args:
        diameter (float): Diameter of the coin.
        height (float): Height of the coin.
        bottom_hatch_width (float): Width and thickness of each bottom hatch line.
        bottom_hatch_spacing (float): Spacing between the center of each bottom hatch line.
        bottom_hatch_depth (float): Depth of the bottom cuts into the bottom of the coin.
        edge_hatch_width (float): Width of each cut in the edge hatch pattern.
        edge_hatch_spacing (float): Spacing between the center of each edge cut.
        edge_hatch_depth (float): Depth of the edge cuts into the side of the coin.
    """
    base = cylinder(d=diameter, h=height)
    cuts = []

    # --- Bottom Hatch ---
    bottom_cuts = []
    num_horizontal_cuts = int(diameter / bottom_hatch_spacing) + 1
    offset_x = -diameter / 2
    for i in range(num_horizontal_cuts):
        x = offset_x + i * bottom_hatch_spacing
        cut = translate((x - bottom_hatch_width / 2, -diameter / 2 - bottom_hatch_depth, 0))(
            linear_extrude(height=bottom_hatch_depth)(
                square(size=(bottom_hatch_width, diameter + 2 * bottom_hatch_depth), center=False)
            )
        )
        bottom_cuts.append(cut)

    num_vertical_cuts = int(diameter / bottom_hatch_spacing) + 1
    offset_y = -diameter / 2
    for i in range(num_vertical_cuts):
        y = offset_y + i * bottom_hatch_spacing
        cut = translate((-diameter / 2 - bottom_hatch_depth, y - bottom_hatch_width / 2, 0))(
            linear_extrude(height=bottom_hatch_depth)(
                square(size=(diameter + 2 * bottom_hatch_depth, bottom_hatch_width), center=False)
            )
        )
        bottom_cuts.append(cut)

    bottom_hatch_cuts = union()(*bottom_cuts)
    cuts.append(translate((0, 0, -bottom_hatch_depth / 2))(bottom_hatch_cuts))

    # --- Edge Hatch ---
    edge_cuts = []
    num_edge_cuts = int(2 * math.pi * diameter / 2 / edge_hatch_spacing)  # Approximate number of cuts

    for i in range(num_edge_cuts):
        angle = i * (360 / num_edge_cuts)
        x = (diameter / 2 + edge_hatch_depth) * math.cos(math.radians(angle))
        y = (diameter / 2 + edge_hatch_depth) * math.sin(math.radians(angle))

        cut = translate((x - edge_hatch_width / 2 * math.cos(math.radians(angle)),
                         y - edge_hatch_width / 2 * math.sin(math.radians(angle)),
                         0))(
            rotate((0, 0, angle))(
                linear_extrude(height=height)(
                    square(size=(edge_hatch_width, edge_hatch_depth + 1), center=False)
                )
            )
        )
        edge_cuts.append(cut)

    edge_hatch_cuts = union()(*edge_cuts)
    cuts.append(edge_hatch_cuts)

    final_base = base - union()(*cuts)
    return final_base


def coin_model(role_name, greyscale_png_filename,
               diameter=50, height=6,
               color_depth=1.0, text_size=4):
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
    coin = cylinder(d=diameter, h=height-0.9)

    # Calculate the XY scale factor so the image fits nicely on the coin.
    scale_factor = calculate_scale_factor(greyscale_png_filename, diameter)

    # Open the image to get the pixel value range.
    # This will be used to normalize the relief height.
    from PIL import Image
    img = Image.open(greyscale_png_filename)
    min_pixel, max_pixel = img.getextrema()  # Example: (47, 255)

    # Compute a z-scale so that the pixel range maps to the desired relief height.
    z_scale = color_depth / 255

    # Create the image relief using SolidPython's surface() function.
    # The 'center=True' option centers the relief geometry.
    image_relief = surface(file=abs_path.name, center=True)

    # Scale the relief in the XY dimensions by the calculated factor and in the Z dimension by z_scale.
    image_relief = scale((scale_factor, scale_factor, z_scale * 2.7))(image_relief)

    # Translate the relief upward so that its base (corresponding to the minimum pixel value)
    # aligns with the top of the coin (z = height).
    image_relief = translate((0, 0, height - color_depth))(image_relief)

    # Extrude a thin shape to cut into the coin
    # image_relief = linear_extrude(height=text_depth)(image_relief)

    # (Optional) Color the relief for debugging; uncomment if needed.
    # image_relief = color("red")(image_relief)

    # Create the engraved text by extruding the role name.
    engraved_text = linear_extrude(height=color_depth)(
        text(role_name, size=text_size, halign="center", valign="center")
    )
    # Position the text so that it is engraved on the lower half of the coin's front.
    engraved_text = translate((0, -diameter / 2 + text_size + 5, height - color_depth))(engraved_text)

    # Subtract both the engraved text and the image relief from the base coin,
    # resulting in an engraved coin.
    final_coin = engraved_text + image_relief
    final_coin = final_coin - coin
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


def create_silhouette_image(input_path, output_path):
    """
    Converts an image to a black-on-white silhouette (useful for subtracting shapes in SCAD).
    - Flattens the image onto a white background (removes transparency).
    - Converts to grayscale, inverts it, then thresholds to pure black & white.
    """
    img = Image.open(input_path).convert("RGBA")

    # Remove transparency by compositing onto a white background
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    composite = Image.alpha_composite(background, img).convert("L")

    # Invert image so that the shape becomes black
    composite = ImageOps.invert(composite)

    # Threshold to black & white
    bw = composite.point(lambda x: 0 if x < 128 else 255, mode='1')

    bw.save(output_path)
    print(f"Silhouette image saved to {output_path}")


def export_coin_to_stl(model, scad_filename="coin.scad", stl_filename="coin.stl"):
    # Convert SCAD to STL using OpenSCAD CLI
    result = subprocess.run([
        "openscad",
        "-o", stl_filename,
        scad_filename
    ], capture_output=True)

    if result.returncode == 0:
        print(f"✅ STL exported successfully: {stl_filename}")
    else:
        print("❌ Error generating STL")
        print(result.stderr.decode())


def main():
    # Load the role data from 'roles.json'.
    with open("roles.json") as f:
        roles = json.load(f)

    # Create output directories for PNGs, greyscale PNGs, and SCAD files if they do not already exist.
    os.makedirs("pngs", exist_ok=True)
    os.makedirs("grey_pngs", exist_ok=True)
    os.makedirs("scads", exist_ok=True)
    os.makedirs("stls", exist_ok=True)

    # Create the base coin stl
    base_model = base_coin_model()
    scad_filename = os.path.join("scads", f"000_coin_base.scad")
    stl_filename = os.path.join("stls", f"000_coin_base.stl")
    scad_render_to_file(base_model, scad_filename, file_header='$fn=100;')
    export_coin_to_stl(base_model, scad_filename, stl_filename)
    print("Generated the base coin scad and stl")

    return

    # Iterate over each role in the JSON map.
    count = 0
    for role, data in roles.items():
        # Create a safe filename by replacing spaces and apostrophes.
        role_safe = role.replace(" ", "_").replace("'", "")
        png_filename = os.path.join("pngs", f"{role_safe}.png")
        grey_png_filename = os.path.join("grey_pngs", f"{role_safe}.png")
        silhouette_png_filename = os.path.join("grey_pngs", f"{role_safe}_silhouette.png")
        scad_filename = os.path.join("scads", f"{role_safe}_coin.scad")
        stl_filename = os.path.join("stls", f"{role_safe}_coin.stl")

        # Download the PNG image if it does not already exist.
        if not os.path.exists(png_filename):
            download_png(data["image"], png_filename)

        # Convert the downloaded PNG image to a greyscale image.
        convert_png_to_greyscale_png(png_filename, grey_png_filename)

        # Create the sillowette image
        create_silhouette_image(png_filename, silhouette_png_filename)

        # Generate the coin model using the greyscale image.
        model = coin_model(role, silhouette_png_filename)

        # Render the coin model to an OpenSCAD (.scad) file.
        scad_render_to_file(model, scad_filename, file_header='$fn=100;')
        print(f"Generated {scad_filename} for role {role}")

        # Export STL file using scad
        export_coin_to_stl(model, scad_filename, stl_filename)
        print(f"Generated {stl_filename} for role {role}")


if __name__ == "__main__":
    main()
