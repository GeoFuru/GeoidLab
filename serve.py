"""Serve GeoidLab locally with HTTP byte-range support for its GeoTIFF grids."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import mimetypes
import os
import shutil
import traceback


class RangeRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        try:
            path = self.translate_path(self.path)
            if os.path.isdir(path):
                return super().send_head()

            f = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None
        except Exception as e:
            print(f"Error opening {self.path}: {e}")
            traceback.print_exc()
            self.send_error(500, "Internal Server Error")
            return None

        try:
            fs = os.fstat(f.fileno())
            size = fs.st_size
            ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
            range_header = self.headers.get("Range")

            if range_header and range_header.startswith("bytes="):
                try:
                    r = range_header[6:]
                    if "-" not in r:
                        raise ValueError
                    first, last = r.split("-", 1)
                    if first:
                        start = int(first)
                        end = min(int(last), size - 1) if last else size - 1
                    else:
                        suf = int(last)
                        start = max(0, size - suf)
                        end = size - 1
                    if start > end or start >= size:
                        raise ValueError
                except ValueError:
                    f.close()
                    self.send_error(416, "Range Not Satisfiable")
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return None

                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                length = end - start + 1
            else:
                self.send_response(200)
                start = 0
                length = size

            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(length))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            f.seek(start)
            self._range_len = length
            return f
        except Exception as e:
            print(f"Error in send_head for {self.path}: {e}")
            traceback.print_exc()
            try:
                f.close()
            except:
                pass
            self.send_error(500, "Internal Server Error")
            return None

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_range_len", None)
        if remaining is None:
            return shutil.copyfileobj(source, outputfile)
        try:
            while remaining > 0:
                chunk = source.read(min(65536, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            print(f"Error in copyfile for {self.path}: {e}")
            traceback.print_exc()

    def handle(self):
        try:
            super().handle()
        except Exception as e:
            print(f"Error in handle: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    try:
        base_dir = Path(__file__).resolve().parent
    except NameError:
        base_dir = Path.cwd()
    print(f"Base dir: {base_dir}")
    os.chdir(base_dir)
    print(f"CWD: {os.getcwd()}")
    server = ThreadingHTTPServer(("127.0.0.1", 8765), RangeRequestHandler)
    print("GeoidLab: http://localhost:8765/")
    print("Serving this project with byte-range support. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGeoidLab server stopped.")
    except Exception as e:
        print(f"Server error: {e}")
        traceback.print_exc()
    finally:
        server.server_close()