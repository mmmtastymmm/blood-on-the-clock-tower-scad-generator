import json
import requests
from bs4 import BeautifulSoup


def get_color_from_style(style):
    """
    Given a style string, return a color name.

    If the color is not known, return "unknown".
    """
    # Ugly brute force that avoids using cssutils.
    style_declarations = style.split(';')
    for declaration in style_declarations:
        if declaration.strip():
            parts = declaration.split(':', 1)
            if len(parts) == 2 and parts[0].strip() == "color":
                color_hex = parts[1].strip()

    if color_hex == "#800080":
        return "purple"
    elif color_hex == "#D4AF37":
        return "yellow"
    elif color_hex == "#3297F4":
        return "blue"
    elif color_hex == "#8C0E12":
        return "red"
    elif color_hex == "#3f9651":
        return "green"
    else:
        print(f"Unknown color: {color_hex}")
        return "unknown"


def main():
    # List of URLs to scrape roles and images from.
    urls_to_parse = [
        "https://wiki.bloodontheclocktower.com/Experimental",
        "https://wiki.bloodontheclocktower.com/Trouble_Brewing",
        "https://wiki.bloodontheclocktower.com/Sects_%26_Violets",
        "https://wiki.bloodontheclocktower.com/Bad_Moon_Rising",
        "https://wiki.bloodontheclocktower.com/Travellers",
        "https://wiki.bloodontheclocktower.com/Fabled",
        "https://wiki.bloodontheclocktower.com/Loric",
    ]

    # Dictionary to hold role data.
    # Each key is a role name and its value is a dict with the image URL and color.
    role_dictionary = {}
    # Process each URL in the urls_to_parse list.
    for url in urls_to_parse:
        # Fetch the page content.
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to load page {url}")

        # Parse the HTML content using BeautifulSoup.
        soup = BeautifulSoup(response.text, "html.parser")

        # Each role is contained in a div with specific classes.
        for container in soup.select("div.small-6.medium-6.large-2.columns"):
            # Look for a span that holds the role name (using the data-role attribute).
            role_span = container.select_one("span[data-role]")
            # Look for the image tag that shows the role's thumbnail.
            image_tag = container.select_one("img.thumbimage")

            # If both the role name and image are found, process them.
            if role_span and image_tag:
                # Extract the role name, trimming any extra whitespace.
                role_name = role_span.get_text(strip=True)
                # Construct the full image URL by prepending the base URL.
                image_src = "https://wiki.bloodontheclocktower.com/" + image_tag.get(
                    "src"
                )
                # Determine the color for this role based on its text style.
                color = get_color_from_style(role_span.get("style"))
                # Save the role's data in the dictionary.
                role_dictionary[role_name] = {"image": image_src, "color": color}

    # Print out the collected roles with their image URLs and colors.
    for role, data in role_dictionary.items():
        image = data["image"]
        color = data["color"]
        print(f"Role: {role}, Image: {image}, Color: {color}")

    # Write the resulting dictionary to a JSON file with pretty-printing.
    with open("roles.json", "w") as role_image_color_json_file:
        json.dump(role_dictionary, role_image_color_json_file, indent=4)


if __name__ == "__main__":
    main()
