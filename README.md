# Blood on the Clock Tower SCAD Generator

For generating SCAD files for Blood on the Clock Tower roles.

## Instructions

1. Install the dependencies in the `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```

2. Generate the role list with the `get_all_roles.py` script:
   ```bash
   python get_all_roles.py
   ```

3. Use the `solid_maker.py` script to make the `scad` files:
   ```bash
   python solid_maker.py
   ```

   To print the role names in another language, pass `--lang`:
   ```bash
   python solid_maker.py --lang es
   ```
   Translated overlays are saved with a language suffix (e.g.
   `stls/blue_Washerwoman_coin_overlay_es.stl`), so English and Spanish tokens can
   be generated side by side. The base coin is shared by all languages. Names that
   are too long to fit around the bottom of the coin are scaled down automatically.

   Note that OpenSCAD finds the font by name, so install
   `assets/Dumbledor1_fixed.ttf` on your system before generating the STLs.

## Translations

Translated role names live in `translations/<lang>.json`, mapping each English role
name to its translation. Available languages:

- `es` (Spanish): names from the [Villa Cuervos wiki](https://villacuervos.es/wiki/).
  Re-generate with `python get_translations.py` when new roles are released.

Any role missing from a translation file falls back to its English name, with a
warning. To add a language, add a `translations/<lang>.json` file with the same
format.

## Development

### Testing

This project uses pytest for testing. To run the tests:

```bash
pytest
```

### Code Formatting

This project uses ruff for code formatting and linting. To check your code:

```bash
ruff format .
```

### Continuous Integration

This project uses GitHub Actions for continuous integration. The CI pipeline:

1. Runs tests with pytest
2. Checks code formatting with ruff

The CI configuration is in `.github/workflows/ci.yml`.
