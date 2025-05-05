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

## Development

### Testing

This project uses pytest for testing. To run the tests:

```bash
pytest
```

### Code Formatting

This project uses ruff for code formatting and linting. To check your code:

```bash
ruff check .
```

### Continuous Integration

This project uses GitHub Actions for continuous integration. The CI pipeline:

1. Runs tests with pytest
2. Checks code formatting with ruff

The CI configuration is in `.github/workflows/ci.yml`.
