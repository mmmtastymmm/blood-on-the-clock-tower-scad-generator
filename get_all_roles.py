import json
import requests
from bs4 import BeautifulSoup


def get_color_from_category(category):
    """
    Given a role category, return a color associated with that category.
    Categories:
      - "Townsfolk" and "Outsiders" are blue.
      - "Minions" and "Demons" are red.
      - "Travellers" or "Travelers" are purple.
      - "Fabled" are yellow.
      - "Loric" are green.
    If the category doesn't match any of these, return "unknown".
    """
    if category in ("Townsfolk", "Outsiders"):
        return "blue"
    elif category in ("Minions", "Demons"):
        return "red"
    elif category in ("Travellers", "Travelers"):
        return "purple"
    elif category == "Fabled":
        return "yellow"
    elif category == "Loric":
        return "green"
    else:
        return "unknown"


def main():
    # List of URLs to scrape roles and images from.
    urls_to_parse = [
        "https://wiki.bloodontheclocktower.com/Experimental",
        "https://wiki.bloodontheclocktower.com/Trouble_Brewing",
        "https://wiki.bloodontheclocktower.com/Sects_%26_Violets",
        "https://wiki.bloodontheclocktower.com/Bad_Moon_Rising",
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
                # Find the nearest preceding h2 element to infer the role category.
                h2 = container.find_previous("h2")
                if h2:
                    category = h2.get_text(strip=True)
                else:
                    category = None
                # Determine the color for this role based on its category.
                color = get_color_from_category(category)
                # Save the role's data in the dictionary.
                role_dictionary[role_name] = {"image": image_src, "color": color}

    # Process the "Travellers" page separately.
    url = "https://wiki.bloodontheclocktower.com/Travellers"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page {url}")

    soup = BeautifulSoup(response.text, "html.parser")

    # For each role container on the Travellers page.
    for container in soup.select("div.small-6.medium-6.large-2.columns"):
        role_span = container.select_one("span[data-role]")
        image_tag = container.select_one("img.thumbimage")

        if role_span and image_tag:
            role_name = role_span.get_text(strip=True)
            image_src = "https://wiki.bloodontheclocktower.com/" + image_tag.get("src")
            # Since all roles on this page are travellers, we set the color to purple.
            color = "purple"
            # Alternatively, you could inspect a style attribute if needed.
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
