import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bigbungi.runtime_assets import asset_specs, cached_asset, prepare_runtime


class RuntimeAssetsTests(unittest.TestCase):
    def fixture(self, root):
        files = {name: name.encode() for name in (
            "pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip",
            "numpy.whl", "pandas.whl",
        )}
        checksum = lambda name: hashlib.sha256(files[name]).hexdigest()
        manifest = {
            "version": "0.27.7", "source": "https://example.invalid/",
            "roots": ["pandas"],
            "runtimeFiles": {name: {"sha256": checksum(name)} for name in files if not name.endswith(".whl")},
            "lock": {"info": {"version": "0.27.7"}, "packages": {
                "numpy": {"file_name": "numpy.whl", "sha256": checksum("numpy.whl"), "depends": []},
                "pandas": {"file_name": "pandas.whl", "sha256": checksum("pandas.whl"), "depends": ["numpy"]},
            }},
        }
        path = root / "manifest.json"
        path.write_text(json.dumps(manifest))
        cache = root / "cache" / manifest["version"]
        cache.mkdir(parents=True)
        for name, data in files.items():
            (cache / name).write_bytes(data)
        return path, manifest, cache

    def test_cached_runtime_publishes_offline_and_repairs_corrupt_public_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, manifest, cache = self.fixture(root)
            with patch("bigbungi.runtime_assets.urlopen", side_effect=AssertionError("Unexpected network request")):
                inventory = prepare_runtime(path, root / "cache", root / "public", offline=True)
                output = root / "public" / manifest["version"]
                self.assertEqual(json.loads((output / "pyodide-lock.json").read_text()), manifest["lock"])
                (output / "numpy.whl").write_bytes(b"broken")
                prepare_runtime(path, root / "cache", root / "public", offline=True)
                self.assertEqual((output / "numpy.whl").read_bytes(), (cache / "numpy.whl").read_bytes())
                self.assertEqual(len(inventory["files"]), 7)
                (cache / "numpy.whl").write_bytes(b"untrusted")
                with self.assertRaisesRegex(RuntimeError, "unavailable offline"):
                    prepare_runtime(path, root / "cache", root / "public", offline=True)

    def test_missing_transitive_packages_and_unsafe_paths_cannot_be_published(self):
        with tempfile.TemporaryDirectory() as directory:
            _, manifest, _ = self.fixture(Path(directory))
            bad = copy.deepcopy(manifest)
            del bad["lock"]["packages"]["numpy"]
            with self.assertRaisesRegex(ValueError, "Missing bundled dependency"):
                asset_specs(bad)
            bad = copy.deepcopy(manifest)
            bad["runtimeFiles"]["../escape"] = {"sha256": "0" * 64}
            with self.assertRaisesRegex(ValueError, "Unsafe asset filename"):
                asset_specs(bad)

    def test_download_checksum_failure_leaves_no_trusted_cache_file(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            spec = {"url": "https://example.invalid/numpy.whl", "sha256": "0" * 64}
            with patch("bigbungi.runtime_assets.urlopen", side_effect=lambda *a, **kw: io.BytesIO(b"corrupt")), patch("bigbungi.runtime_assets.time.sleep"):
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    cached_asset("numpy.whl", spec, cache)
            self.assertEqual(list(cache.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
