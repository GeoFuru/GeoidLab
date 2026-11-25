
from pathlib import Path
import math
import sys

import numpy as np
import tifffile


BASE_DIR = Path(__file__).resolve().parent
GRID_DIR = BASE_DIR / "Grids"

POINTS = [
    {"id": "RGI1", "lat": -38.7250234944, "lon": -72.6327324917},
    {"id": "RGI2", "lat": -38.7253842167, "lon": -72.6314060278},
    {"id": "RGI3", "lat": -38.7255555556, "lon": -72.6303456556},
    {"id": "RGI4", "lat": -38.7261044389, "lon": -72.6316106861},
    {"id": "RGI5", "lat": -38.7259296639, "lon": -72.6328612806},
    {"id": "RGI6", "lat": -38.7252456667, "lon": -72.6336456361},
]

REFERENCE = {
    "EGM2008": [17.9398, 17.9418, 17.9435, 17.9405, 17.9385, 17.9379],
    "EGM96":   [18.1506, 18.1746, 18.1766, 18.1730, 18.1706, 18.1699],
    "EGM84":   [17.6357, 17.6417, 17.6465, 17.6413, 17.6357, 17.6318],
}

MODELS = {
    "EGM2008": "us_nga_egm2008_25.tif",
    "EGM96": "us_nga_egm96_15.tif",
    "EGM84": "us_nga_egm84_30.tif",
}


def get_tag(page, tag_id):
    tag = page.tags.get(tag_id)
    if tag is None:
        raise ValueError(f"Missing TIFF tag: {tag_id}")
    return tag.value


def get_raster_type(page):
    keys = get_tag(page, 34735)
    number_of_keys = keys[3]

    for index in range(number_of_keys):
        offset = 4 + index * 4
        key_id, location, count, value = keys[offset:offset + 4]

        if key_id == 1025 and location == 0 and count == 1:
            return value

    raise ValueError("GeoTIFF RasterType key not found")


def load_grid(path):
    with tifffile.TiffFile(path) as tif:
        page = tif.pages[0]

        if len(tif.pages) != 1:
            raise ValueError("Expected a single-page TIFF")

        raster = page.asarray()

        if raster.ndim != 2:
            raise ValueError(f"Expected a 2D raster, got {raster.shape}")

        raster = np.asarray(raster, dtype=np.float64)

        scale = get_tag(page, 33550)
        tiepoint = get_tag(page, 33922)
        raster_type = get_raster_type(page)

        nodata_tag = page.tags.get(42113)
        nodata = -32767.0

        if nodata_tag is not None:
            value = nodata_tag.value
            if isinstance(value, bytes):
                value = value.decode("ascii").strip("\x00")
            nodata = float(value)

        if raster_type != 2:
            raise ValueError(
                f"Expected PixelIsPoint (2), found RasterType={raster_type}"
            )

        pixel_x, pixel_y = float(scale[0]), float(scale[1])

        if pixel_x <= 0 or pixel_y <= 0:
            raise ValueError("Invalid pixel scale")

        i, j, _, x, y, _ = map(float, tiepoint[:6])

        if i != 0 or j != 0:
            raise ValueError("Unexpected TIFF tiepoint origin")

        origin_lon = x
        origin_lat = y

    return raster, origin_lon, origin_lat, pixel_x, pixel_y, nodata


def bilinear(raster, lon, lat, origin_lon, origin_lat,
             pixel_x, pixel_y, nodata):

    col = (lon - origin_lon) / pixel_x
    row = (origin_lat - lat) / pixel_y

    col0 = math.floor(col)
    row0 = math.floor(row)

    dx = col - col0
    dy = row - row0

    if (
        row0 < 0 or col0 < 0
        or row0 + 1 >= raster.shape[0]
        or col0 + 1 >= raster.shape[1]
    ):
        raise ValueError("Point outside raster boundaries")

    nw = raster[row0, col0]
    ne = raster[row0, col0 + 1]
    sw = raster[row0 + 1, col0]
    se = raster[row0 + 1, col0 + 1]

    values = np.array([nw, ne, sw, se])

    if not np.all(np.isfinite(values)):
        raise ValueError("Invalid raster values")

    if np.any(values == nodata):
        raise ValueError("Interpolation includes NoData")

    north = nw * (1 - dx) + ne * dx
    south = sw * (1 - dx) + se * dx

    return north * (1 - dy) + south * dy


def main():
    print("=" * 65)
    print("GEIODLAB - NUMPY INDEPENDENT VALIDATION")
    print("=" * 65)

    for model, filename in MODELS.items():
        path = GRID_DIR / filename

        print(f"\n{'=' * 65}")
        print(model)
        print("=" * 65)

        if not path.exists():
            print(f"ERROR: Grid not found: {path}")
            continue

        try:
            raster, lon0, lat0, dx, dy, nodata = load_grid(path)

            print(f"Grid dimensions: {raster.shape[1]} x {raster.shape[0]}")
            print(f"Pixel size: {dx:.10f}, {dy:.10f}")
            print(f"Raster origin: {lon0}, {lat0}")
            print("Interpolation: Bilinear")
            print()

            reference_values = REFERENCE[model]
            differences = []

            for index, point in enumerate(POINTS):
                result = bilinear(
                    raster,
                    point["lon"],
                    point["lat"],
                    lon0,
                    lat0,
                    dx,
                    dy,
                    nodata,
                )

                reference = reference_values[index]
                difference = result - reference
                differences.append(abs(difference))

                print(
                    f"{point['id']}: "
                    f"N = {result:.9f} m | "
                    f"GeoIDLab = {reference:.4f} m | "
                    f"Delta = {difference:+.9f} m"
                )

            max_difference = max(differences)

            print(f"\nMaximum absolute difference: {max_difference:.9f} m")

            if max_difference <= 0.0001:
                print("RESULT: PASS")
            else:
                print("RESULT: REVIEW REQUIRED")

        except Exception as error:
            print(f"ERROR: {error}")
            continue

    print("\nValidation completed.")


if __name__ == "__main__":
    main()
