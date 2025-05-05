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


def base_coin_model(diameter=45, height=4):
    """
    Creates the base coin model with the botc logo cut into the base
    and small groves cut into the edge of the coin.
    """
    base = cylinder(d=diameter, h=height)

    # --- Botc Logo ---
    botc_svg_filename = "botc_45.svg"
    shutil.copy(botc_svg_filename, "scads")

    svg_size_cm = 4.5

    # Import the SVG file as a 2D shape.
    svg_shape = import_(botc_svg_filename, convexity=10)

    # Center the scaled SVG shape.
    # calculate centering offset in mm
    centering_offset = svg_size_cm * 10.0 / 2.0
    centered_svg = translate((-centering_offset, -centering_offset, 0))(svg_shape)

    # Extrude the centered and scaled SVG shape.
    extrude_height = 0.4
    extruded_svg = linear_extrude(height=extrude_height)(centered_svg)

    # --- Edge Hatch ---
    edge_hatch_width = 3
    edge_hatch_spacing = 10
    edge_hatch_depth = 1
    edge_cuts = []
    num_edge_cuts = int(
        2 * math.pi * diameter / 2 / edge_hatch_spacing
    )  # Approximate number of cuts

    for i in range(num_edge_cuts):
        angle = i * (360 / num_edge_cuts)
        x = (diameter / 2 + edge_hatch_depth) * math.cos(math.radians(angle))
        y = (diameter / 2 + edge_hatch_depth) * math.sin(math.radians(angle))

        cut = translate(
            (
                x - edge_hatch_width / 2 * math.cos(math.radians(angle)),
                y - edge_hatch_width / 2 * math.sin(math.radians(angle)),
                0,
            )
        )(
            rotate((0, 0, angle))(
                linear_extrude(height=height)(
                    square(size=(edge_hatch_width, edge_hatch_depth + 1), center=False)
                )
            )
        )
        edge_cuts.append(cut)
    edge_hatch_cuts = union()(*edge_cuts)

    final_base = base - extruded_svg - edge_hatch_cuts
    return final_base


def role_overlay_model(
    role_name, svg_filename, diameter=45, height=4, extrude_height=0.2, text_size=4
):
    """
    Creates a colored overlay model add to the coin with the role name and image.
    """
    # Convert the image file path to an absolute path with forward slashes.
    abs_path = Path(os.path.abspath(svg_filename).replace("\\", "/"))
    shutil.copy(svg_filename, "scads")
    print(f"Copied {svg_filename} to scads directory for use in OpenSCAD.")

    # Create the base coin as a simple cylinder.
    coin = cylinder(d=diameter, h=height - 0.9)

    svg_size_cm = 4.5
    scale_factor = 1.0

    # Import the SVG file as a 2D shape.
    svg_shape = import_(abs_path.name, convexity=10)

    # Scale the imported SVG shape.
    scaled_svg = scale((scale_factor, scale_factor, 0))(svg_shape)

    # Center the scaled SVG shape.
    # calculate centering offset in mm
    centering_offset = svg_size_cm * scale_factor * 10.0 / 2.0
    centered_svg = translate((-centering_offset, -centering_offset, 0))(scaled_svg)

    # Extrude the centered and scaled SVG shape.
    extruded_svg = linear_extrude(height=extrude_height)(centered_svg)

    # Translate the extruded svg to the top of the coin
    extruded_svg = translate((0, 0, height - extrude_height))(extruded_svg)

    # --- Curved Text ---
    char_spacing = 10  # Adjust as needed
    radius = diameter / 2 - 2  # Adjust radius to bring text closer to the edge
    text_angle = 270  # Start at the bottom
    total_angle = (len(role_name) - 1) * char_spacing
    start_angle = text_angle - total_angle / 2

    text_parts = []
    for i, char in enumerate(role_name):
        char_angle = start_angle + i * char_spacing
        x = radius * math.cos(math.radians(char_angle))
        y = radius * math.sin(math.radians(char_angle))

        # Use rotate_extrude for 3D text and rotate each character so its top points outward
        character = text(
            char,
            font="Trade Gothic LT Std",
            size=text_size,
            halign="center",
            valign="bottom",
        )
        char_3d = linear_extrude(height=extrude_height)(character)
        rotated_char = translate((x, y, height - extrude_height))(
            rotate(a=char_angle + 90, v=[0, 0, 1])(char_3d)
        )  # add 90 to the rotation
        text_parts.append(rotated_char)

    curved_text = union()(*text_parts)

    # Combine the extruded svg and text for the overlay.
    overlay_design = extruded_svg + curved_text

    return overlay_design


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
    bw = composite.point(lambda x: 0 if x < 128 else 255, mode="1")

    bw.save(output_path)
    print(f"Silhouette image saved to {output_path}")


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

        # 2. Convert PBM to svg using Potrace
        subprocess.run(
            [
                "potrace",
                pbm_path,
                "-o",
                svg_path,
                "--svg",
                "-W",
                "4.5cm",
                "-H",
                "4.5cm",
            ],
            check=True,
            capture_output=True,
        )
        print(f"Converted {pbm_path} to {svg_path} using Potrace")

        return True  # Indicate success

    except subprocess.CalledProcessError as e:
        print(f"Error converting to svg: {e.stderr.decode()}")
        return False
    except FileNotFoundError as e:
        print(
            f"Error: {e.strerror}.  Please ensure ImageMagick and Potrace are installed and in your PATH."
        )
        return False


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

    base_model = base_coin_model()
    base_scad_filename = os.path.join("scads", f"000_coin_base.scad")
    base_stl_filename = os.path.join("stls", f"000_coin_base.stl")
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
        create_silhouette_image(png_filename, f"{grey_png_filename}_silhouette.png")

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
