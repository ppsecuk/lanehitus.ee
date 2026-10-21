"""Build content-addressed WebP previews without changing the image originals.

Install website/requirements-build.txt into a virtual environment, then run
python website/optimize_images.py. Use --check to verify the checked-in outputs.
The HTML builder consumes image-assets.json and needs no Pillow installation.
"""

from __future__ import annotations

import argparse
import ast
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "website/image-assets.json"
OUTPUT = ROOT / "images/optimized"
QUALITY = 82
METHOD = 6
PORTRAIT = "images/about/anatoli-portrait.png"
LOGO = "images/brand/lan-ehitus-original.jpeg"


def gallery_sources() -> list[str]:
    """Read only the literal gallery declaration; build.py has write side effects."""
    tree = ast.parse((ROOT / "website/build.py").read_text(encoding="utf-8"))
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "gallery_photos"
    )
    returns = [node for node in function.body if isinstance(node, ast.Return)]
    if len(returns) != 1:
        raise ValueError("gallery_photos must return one literal dictionary")
    galleries = ast.literal_eval(returns[0].value)
    if not isinstance(galleries, dict):
        raise ValueError("gallery_photos must return a dictionary")
    sources = []
    for photos in galleries.values():
        if not isinstance(photos, (list, tuple)):
            raise ValueError("Each gallery must contain a list of photos")
        for photo in photos:
            if not isinstance(photo, (list, tuple)) or len(photo) != 3:
                raise ValueError("Gallery entries must contain path, alt and position")
            if not isinstance(photo[0], str):
                raise ValueError("Gallery source paths must be strings")
            sources.append(photo[0])
    return sorted(set(sources))


def source_path(relative: str) -> Path:
    candidate = Path(relative)
    if not candidate.parts or candidate.is_absolute() or ".." in candidate.parts or candidate.parts[0] != "images":
        raise ValueError(f"Image path must stay in the repository images directory: {relative}")
    resolved = (ROOT / candidate).resolve(strict=True)
    if not resolved.is_relative_to(ROOT / "images") or not resolved.is_file():
        raise ValueError(f"Image path must resolve to a file in images: {relative}")
    return resolved


def widths_for(relative: str, source_width: int) -> list[int]:
    widths = (240, 480) if relative == PORTRAIT else (192, 384) if relative == LOGO else (480, 960, 1280)
    # Include the original width when it is smaller than a requested variant;
    # set() avoids duplicate files, and min() prevents upscaling.
    return sorted({min(width, source_width) for width in widths})


def encode_preview(image: Image.Image, width: int) -> tuple[bytes, int]:
    height = max(1, round(image.height * width / image.width))
    resized = image.resize((width, height), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    # Deliberately omit EXIF, ICC and other source metadata from public previews.
    resized.save(buffer, format="WEBP", quality=QUALITY, method=METHOD)
    content = buffer.getvalue()
    with Image.open(BytesIO(content)) as decoded:
        decoded.load()
        if decoded.format != "WEBP" or decoded.size != (width, height):
            raise ValueError("Encoded preview did not decode to its expected dimensions")
    return content, height


def build(*, check: bool) -> dict:
    if OUTPUT.is_symlink() or not OUTPUT.resolve().is_relative_to(ROOT / "images"):
        raise ValueError("Optimized output directory must stay in repository images")
    if MANIFEST.is_symlink():
        raise ValueError("Image manifest must not be a symlink")
    sources = gallery_sources()
    selected = sorted(set(sources + [PORTRAIT, LOGO]))
    manifest = {}
    original_bytes = 0
    changed = []
    for relative in selected:
        source = source_path(relative)
        original_bytes += source.stat().st_size
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
        variants = []
        for width in widths_for(relative, image.width):
            content, height = encode_preview(image, width)
            fingerprint = sha256(content).hexdigest()[:16]
            name = f"{source.stem}-{width}w-{fingerprint}.webp"
            destination = OUTPUT / name
            if destination.is_symlink():
                raise ValueError(f"Optimized asset must not be a symlink: {name}")
            if destination.exists():
                if destination.read_bytes() != content:
                    raise ValueError(f"Content hash collision or modified asset: {name}")
            else:
                changed.append(destination.relative_to(ROOT).as_posix())
                if not check:
                    OUTPUT.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(content)
            variants.append({
                "path": destination.relative_to(ROOT).as_posix(),
                "width": width,
                "height": height,
                "bytes": len(content),
            })
        manifest[relative] = {"variants": variants, "width": image.width, "height": image.height}

    serialized = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if not MANIFEST.exists() or MANIFEST.read_text(encoding="utf-8") != serialized:
        changed.append(MANIFEST.relative_to(ROOT).as_posix())
        if not check:
            MANIFEST.write_text(serialized, encoding="utf-8")
    if check and changed:
        raise ValueError("Optimized outputs are outdated or missing:\n" + "\n".join(changed))

    total_variants = sum(len(entry["variants"]) for entry in manifest.values())
    largest_bytes = sum(entry["variants"][-1]["bytes"] for entry in manifest.values())
    smallest_bytes = sum(entry["variants"][0]["bytes"] for entry in manifest.values())
    print(f"{'Verified' if check else 'Built'} {total_variants} WebP variants for {len(selected)} originals")
    print(f"Originals: {original_bytes:,} bytes; largest previews: {largest_bytes:,} bytes "
          f"({(1 - largest_bytes / original_bytes):.1%} smaller); smallest previews: {smallest_bytes:,} bytes")
    print(f"Files {'needing changes' if check else 'changed'}: {len(changed)}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify outputs without writing files")
    arguments = parser.parse_args()
    try:
        build(check=arguments.check)
    except (OSError, ValueError, SyntaxError, StopIteration) as error:
        parser.exit(1, f"Image optimization failed: {error}\n")
