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
from PIL import Image, ImageOps, ImageFont


# Dimensional constants in mm
COIN_DIAMETER = 45
COIN_HEIGHT = 2
LOGO_EXTRUDE_DEPTH = 0.6
ROLE_EXTRUDE_DEPTH = 0.2
FONT = "Dumbledor1"
TEXT_SIZE = 4


def get_relative_widths_pillow(font_path, font_size, characters):
    """
    Calculates the relative widths of characters in a proportional font using Pillow.

    Args:
        font_path (str): The path to the font file (e.g., .ttf, .otf).
        font_size (int): The size of the font in points.
        characters (str): A string containing the characters to measure.

    Returns:
        dict: A dictionary where keys are characters and values are their widths.
    """
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"Error: Font file not found at {font_path}")
        return {}

    widths = {}
    for char in characters:
        width, height = font.getbbox(char)[2:4]  # Get width from the bounding box
        widths[char] = width
    return widths


def felt_coin_model():
    """
    Creates the base coin model with the botc logo cut into the base
    and small groves cut into the edge of the coin.
    """
    return cylinder(d=COIN_DIAMETER, h=COIN_HEIGHT)


def logo_coin_model():
    """
    Creates the base coin model with the botc logo cut into the base
    and small groves cut into the edge of the coin.
    """
    base = cylinder(d=COIN_DIAMETER, h=COIN_HEIGHT)

    # --- Botc Logo ---
    # Copy into the scads directory so we can import it in the scad file
    botc_svg = "assets/botc.svg"
    shutil.copy(botc_svg, "scads")

    # Import the SVG file as a 2D shape.
    svg_shape = import_(os.path.basename(botc_svg), convexity=10)

    # Center the scaled SVG shape.
    # calculate centering offset in mm
    centering_offset = COIN_DIAMETER / 2.0
    centered_svg = translate((-centering_offset, -centering_offset, 0))(svg_shape)

    # Extrude the centered and scaled SVG shape.
    extruded_svg = linear_extrude(height=LOGO_EXTRUDE_DEPTH)(centered_svg)

    # --- Edge Hatch ---
    edge_hatch_width = 3
    edge_hatch_spacing = 10
    edge_hatch_depth = 1
    edge_cuts = []
    num_edge_cuts = int(
        2 * math.pi * COIN_DIAMETER / 2 / edge_hatch_spacing
    )  # Approximate number of cuts

    for i in range(num_edge_cuts):
        angle = i * (360 / num_edge_cuts)
        x = (COIN_DIAMETER / 2 + edge_hatch_depth) * math.cos(math.radians(angle))
        y = (COIN_DIAMETER / 2 + edge_hatch_depth) * math.sin(math.radians(angle))

        cut = translate(
            (
                x - edge_hatch_width / 2 * math.cos(math.radians(angle)),
                y - edge_hatch_width / 2 * math.sin(math.radians(angle)),
                0,
            )
        )(
            rotate((0, 0, angle))(
                linear_extrude(height=COIN_HEIGHT)(
                    square(size=(edge_hatch_width, edge_hatch_depth + 1), center=False)
                )
            )
        )
        edge_cuts.append(cut)
    edge_hatch_cuts = union()(*edge_cuts)

    return base - extruded_svg - edge_hatch_cuts


def role_overlay_model(
    role_name,
    svg_filename,
):
    """
    Creates a colored overlay model add to the coin with the role name and image.
    """
    # Convert the image file path to an absolute path with forward slashes.
    shutil.copy(svg_filename, "scads")
    print(f"Copied {svg_filename} to scads directory for use in OpenSCAD.")

    # Import the SVG file as a 2D shape.
    svg_shape = import_(os.path.basename(svg_filename), convexity=10)

    # Center the scaled SVG shape.
    centering_offset = COIN_DIAMETER / 2.0
    centered_svg = translate((-centering_offset, -centering_offset, 0))(svg_shape)

    # Extrude the centered and scaled SVG shape.
    extruded_svg = linear_extrude(height=ROLE_EXTRUDE_DEPTH)(centered_svg)

    # Translate the extruded svg to the top of the coin
    extruded_svg = translate((0, 0, COIN_HEIGHT - ROLE_EXTRUDE_DEPTH))(extruded_svg)

    # --- Curved Text ---
    # Calculate the width of characters, note that 5x - 2 the text size was found to be
    # a good function for translating pixels of text into angle distance through
    # trial and error.
    printed_role_name = role_name.upper()
    font_file = "assets/Trade Gothic LT Std Regular/Trade Gothic LT Std Regular.otf"
    relative_widths = get_relative_widths_pillow(
        font_file, TEXT_SIZE * 5 - 2, printed_role_name
    )

    radius = COIN_DIAMETER / 2 - 2  # Adjust radius to bring text closer to the edge
    text_angle = 270  # Start at the bottom

    # calculate the total angle so we know where to start rendering characters
    average_char_width = sum([relative_widths[c] for c in printed_role_name]) / len(
        role_name
    )
    total_angle = (len(role_name) - 1) * average_char_width
    start_angle = text_angle - total_angle / 2

    text_parts = []
    char_angle = start_angle
    previons_width = 0
    for i, char in enumerate(printed_role_name):
        # Advance the position of the character except in the case of the first
        # character where our previous width was 0.
        # We do this by averaging the width of this character and the one before it
        # as the angle where we render the character can be thought of the point
        # along the curve it is rendered in the center bottom edge of the character.
        if previons_width != 0:
            char_angle += sum([previons_width, relative_widths[char]]) / 2.0

        x = radius * math.cos(math.radians(char_angle))
        y = radius * math.sin(math.radians(char_angle))

        # Use rotate_extrude for 3D text and rotate each character so its top points outward
        character = text(
            char,
            font=FONT,
            size=TEXT_SIZE,
            halign="center",
            valign="bottom",
        )
        char_3d = linear_extrude(height=ROLE_EXTRUDE_DEPTH)(character)
        rotated_char = translate((x, y, COIN_HEIGHT - ROLE_EXTRUDE_DEPTH))(
            rotate(a=char_angle + 90, v=[0, 0, 1])(char_3d)
        )  # add 90 to the rotation
        text_parts.append(rotated_char)
        previons_width = relative_widths[char]

    curved_text = union()(*text_parts)

    # Combine the extruded svg and text for the overlay.
    return extruded_svg + curved_text


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


def convert_to_svg_with_potrace(png_path, svg_path):
    """
    Converts a PNG image to an svg file using ImageMagick and Potrace.
    Requires ImageMagick and Potrace to be installed and in the system's PATH.
    """
    try:
        # 1. Convert PNG to PBM (Portable Bitmap) using ImageMagick
        pbm_path = png_path.replace(".png", ".pbm")  # Create a .pbm filename
        subprocess.run(
            [
                "convert",
                png_path,
                "-monochrome",
                pbm_path,
            ],  # "-monochrome" for black/white
            check=True,
            capture_output=True,
        )
        print(f"Converted {png_path} to {pbm_path}")

        dimension = "{:.2f}cm".format(COIN_DIAMETER / 10)

        # 2. Convert PBM to svg using Potrace
        subprocess.run(
            [
                "potrace",
                pbm_path,
                "-o",
                svg_path,
                "--svg",
                "-W",
                dimension,
                "-H",
                dimension,
            ],
            check=True,
            capture_output=True,
        )
        print(f"Converted {pbm_path} to {svg_path} using Potrace")

    except subprocess.CalledProcessError as e:
        print(f"Error converting to svg: {e.stderr.decode()}")
    except FileNotFoundError as e:
        print(
            f"Error: {e.strerror}.  Please ensure ImageMagick and Potrace are installed and in your PATH."
        )


def export_coin_to_stl(model, scad_filename="coin.scad", stl_filename="coin.stl"):
    # Convert SCAD to STL using OpenSCAD CLI
    result = subprocess.run(
        ["openscad", "-o", stl_filename, scad_filename], capture_output=True
    )

    if result.returncode == 0:
        print(f"✅ STL exported successfully: {stl_filename}")
    else:
        print("❌ Error generating STL")
        print(result.stderr.decode())


def main():
    with open("roles.json") as f:
        roles = json.load(f)

    os.makedirs("pngs", exist_ok=True)
    os.makedirs("grey_pngs", exist_ok=True)
    os.makedirs("svgs", exist_ok=True)
    os.makedirs("scads", exist_ok=True)
    os.makedirs("stls", exist_ok=True)

    base_model = felt_coin_model()
    base_scad_filename = os.path.join("scads", f"000_coin_base_2mm_felt.scad")
    base_stl_filename = os.path.join("stls", f"000_coin_base_2mm_felt.stl")
    scad_render_to_file(base_model, base_scad_filename, file_header="$fn=100;")
    export_coin_to_stl(base_model, base_scad_filename, base_stl_filename)
    print("Generated the base coin scad and stl")

    for role, data in roles.items():
        color = data["color"]
        role_safe = role.replace(" ", "_").replace("'", "")
        png_filename = os.path.join("pngs", f"{role_safe}.png")
        grey_png_filename = os.path.join("grey_pngs", f"{role_safe}.png")
        svg_filename = os.path.join("svgs", f"{role_safe}.svg")
        overlay_scad_filename = os.path.join("scads", f"{role_safe}_coin_overlay.scad")
        overlay_stl_filename = os.path.join(
            "stls", f"{color}_{role_safe}_coin_overlay.stl"
        )

        if not os.path.exists(png_filename):
            download_png(data["image"], png_filename)
        convert_png_to_greyscale_png(png_filename, grey_png_filename)

        # Convert the grayscale PNG to svg using ImageMagick and Potrace
        convert_to_svg_with_potrace(grey_png_filename, svg_filename)

        overlay_model = role_overlay_model(role, svg_filename)

        scad_render_to_file(
            overlay_model, overlay_scad_filename, file_header="$fn=100;"
        )
        print(f"Generated {overlay_scad_filename} for role {role} overlay")

        export_coin_to_stl(overlay_model, overlay_scad_filename, overlay_stl_filename)
        print(f"Generated {overlay_stl_filename} for role {role} overlay")


if __name__ == "__main__":
    main()
