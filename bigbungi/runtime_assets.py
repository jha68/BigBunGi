"""Publish a pinned, same-origin Pyodide distribution using only the stdlib.

Downloads happen at build time. Browsers load the runtime and every supported
package from the Pages site, including dependencies and third-party licenses.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "web" / "pyodide-manifest.json"
MAX_FILE_BYTES = 96 * 1024 * 1024


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def asset_specs(manifest):
    """Validate the dependency closure before downloading or publishing files."""
    version = manifest["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Invalid Pyodide version")
    lock = manifest["lock"]
    if lock["info"]["version"] != version:
        raise ValueError("Runtime and package index versions differ")
    packages = lock["packages"]
    visited = set()

    def visit(name):
        if name in visited:
            return
        if name not in packages:
            raise ValueError(f"Missing bundled dependency: {name}")
        visited.add(name)
        for dependency in packages[name].get("depends", []):
            visit(dependency)

    for name in manifest["roots"]:
        visit(name)
    if visited != set(packages):
        raise ValueError("Package index contains unbundled or unused entries")
    specs = dict(manifest["runtimeFiles"])
    for package in packages.values():
        specs[package["file_name"]] = {"sha256": package["sha256"]}
    for name, spec in specs.items():
        if Path(name).name != name or name in (".", "..") or "\\" in name:
            raise ValueError(f"Unsafe asset filename: {name}")
        if not re.fullmatch(r"[a-f0-9]{64}", spec["sha256"]):
            raise ValueError(f"Missing asset checksum: {name}")
        spec = specs[name] = dict(spec)
        spec.setdefault("url", manifest["source"] + name)
        if not spec["url"].startswith("https://"):
            raise ValueError("Runtime downloads must use HTTPS")
    for name in ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip"):
        if name not in specs:
            raise ValueError(f"Missing runtime file: {name}")
    return specs


def cached_asset(name, spec, cache, offline=False):
    target = cache / name
    if target.is_file() and digest(target) == spec["sha256"]:
        return target
    if offline:
        raise RuntimeError(f"Verified runtime asset unavailable offline: {name}")
    for attempt in range(3):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=cache, delete=False) as handle:
                temporary = Path(handle.name)
                size = 0
                with urlopen(spec["url"], timeout=45) as response:
                    while chunk := response.read(1024 * 1024):
                        size += len(chunk)
                        if size > MAX_FILE_BYTES:
                            raise ValueError(f"Runtime file exceeds static-host file limit: {name}")
                        handle.write(chunk)
            if digest(temporary) != spec["sha256"]:
                raise ValueError(f"SHA-256 mismatch for {name}")
            if "size" in spec and size != spec["size"]:
                raise ValueError(f"Unexpected size for {name}")
            temporary.replace(target)
            return target
        except Exception:
            if attempt == 2:
                raise
            time.sleep(0.5 * (attempt + 1))
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def prepare_runtime(manifest_path=MANIFEST, cache_root=None, public_root=None, offline=False):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    specs = asset_specs(manifest)
    version = manifest["version"]
    cache = Path(cache_root or ROOT / ".runtime" / "pyodide") / version
    output = Path(public_root or ROOT / "web" / "public" / "pyodide") / version
    cache.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(cached_asset, name, spec, cache, offline): name for name, spec in specs.items()}
        for future in as_completed(futures):
            future.result()
    lock_bytes = (json.dumps(manifest["lock"], indent=2, sort_keys=True) + "\n").encode()
    inventory = {
        "version": version,
        "roots": manifest["roots"],
        "packages": sorted(manifest["lock"]["packages"]),
        "files": [{"name": name, "sha256": spec["sha256"], "bytes": (cache / name).stat().st_size} for name, spec in sorted(specs.items())] +
                 [{"name": "pyodide-lock.json", "sha256": hashlib.sha256(lock_bytes).hexdigest(), "bytes": len(lock_bytes)}],
    }
    # Recheck published files too; a stale or incomplete folder cannot pass a build.
    if not all((output / f["name"]).is_file() and digest(output / f["name"]) == f["sha256"] for f in inventory["files"]):
        output.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{version}-", dir=output.parent))
        try:
            for name in specs:
                shutil.copyfile(cache / name, staging / name)
            (staging / "pyodide-lock.json").write_bytes(lock_bytes)
            if output.exists():
                shutil.rmtree(output)
            staging.replace(output)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    (output / "manifest.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    size = sum(file["bytes"] for file in inventory["files"])
    print(f"Same-origin Pyodide {version}: {len(inventory['files'])} verified files, {len(inventory['packages'])} packages, {size / 1024**2:.1f} MiB", flush=True)
    return inventory


if __name__ == "__main__":
    import sys
    prepare_runtime(offline="--offline" in sys.argv)
