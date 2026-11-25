"""Serve GeoidLab locally with HTTP byte-range support for its GeoTIFF grids."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import mimetypes
import os
import shutil


class RangeRequestHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        try:
            file_handle = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        size = os.fstat(file_handle.fileno()).st_size
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        range_header = self.headers.get("Range")
        start, end = 0, size - 1

        if range_header and range_header.startswith("bytes="):
            try:
                first, last = range_header[6:].split("-", 1)
                if first:
                    start = int(first)
                    end = min(int(last), size - 1) if last else size - 1
                else:
                    suffix_length = int(last)
                    start = max(0, size - suffix_length)
                if start > end or start >= size:
                    raise ValueError
            except ValueError:
                file_handle.close()
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return None

            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)

        self.send_header("Content-type", content_type)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Last-Modified", self.date_time_string(os.path.getmtime(path)))
        self.end_headers()
        file_handle.seek(start)
        self.range_remaining = end - start + 1
        return file_handle

    def copyfile(self, source, output):
        remaining = getattr(self, "range_remaining", None)
        if remaining is None:
            return shutil.copyfileobj(source, output)
        while remaining:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            output.write(chunk)
            remaining -= len(chunk)


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    server = ThreadingHTTPServer(("127.0.0.1", 8765), RangeRequestHandler)
    print("GeoidLab: http://localhost:8765/")
    print("Serving this project with byte-range support. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGeoidLab server stopped.")
    finally:
        server.server_close()