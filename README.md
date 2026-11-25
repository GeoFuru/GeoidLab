# GeoIDLab

Browser-based geoid calculator and comparison tool for EGM84, EGM96, and EGM2008. It supports bilinear and bicubic interpolation, CSV processing, map-based profiles, and Agisoft and GeographicLib grids.

## Run locally

Requires Python 3. From this folder, run:

```bash
python3 serve.py
```

Then open <http://localhost:8765/>. The local server supports HTTP byte-range requests used to read the GeoTIFF grids. You can also use another HTTP server with byte-range support.

## Included grids

The app includes Agisoft and GeographicLib grids for EGM2008 (2.5′), EGM96 (15′), and EGM84 (30′). GeographicLib PGM source samples were converted to GeoTIFF while preserving their samples and scale/offset metadata. The source archives are not required at runtime. See the [GeographicLib geoid documentation](https://geographiclib.sourceforge.io/C++/doc/geoid.html)

## Validation

The independent NumPy and GDAL bilinear cross-check covered six points for all three models. It reproduced GeoIDLab's geoid undulations to the displayed precision. The validation script is in `Validations/`.

