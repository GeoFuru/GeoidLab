# GeoIDLab

Browser-based geoid calculator and comparison tool for EGM84, EGM96, and EGM2008. It supports bilinear and bicubic interpolation, CSV processing, map-based profiles, and Agisoft and GeographicLib grids.

## Run locally

Requires Python 3. From this folder, run:

```bash
python3 serve.py
```

Then open <http://localhost:8765/>. The local server supports HTTP byte-range requests used to read the GeoTIFF grids. You can also use another HTTP server with byte-range support.

## Publish with GitHub Pages

Push this repository to GitHub, then select **Settings → Pages** and publish the `main` branch from the repository root. GitHub Pages serves `index.html`, which opens `geoidlab.html`. Keep the `Grids/` folder and its filenames intact. The page loads GeoTIFF.js and Leaflet from public CDNs, so visitors need an internet connection.

## Included grids

The app includes Agisoft and GeographicLib grids for EGM2008 (2.5′), EGM96 (15′), and EGM84 (30′). GeographicLib PGM source samples were converted to GeoTIFF while preserving their samples and scale/offset metadata. The source archives are not required at runtime. See the [GeographicLib geoid documentation](https://geographiclib.sourceforge.io/C++/doc/geoid.html).

The 1′ EGM2008 grid is excluded because this app does not use it and the file exceeds GitHub's 100 MB per-file limit. `.gitignore` also excludes local environments, private working notes, installers, source archives, and generated auxiliary files.

## Validation

The independent NumPy and GDAL bilinear cross-check covered six points for all three models. It reproduced GeoIDLab's geoid undulations to the displayed precision. The validation script is in `Validations/`.

## License

No license is declared yet. Before redistributing the project or its grids, add a `LICENSE` after confirming the applicable terms for each component and dataset.
