from cairosvg import svg2png
from pathlib import Path


# deleted path so i can use it again for other stuff
svg_folder = Path("")
output_folder = Path("")
output_folder.mkdir(exist_ok=True)

for svg_file in svg_folder.glob("*.svg"):
    with open(svg_file, "rb") as f:
        svg_data = f.read()

    png_file = output_folder / f"{svg_file.stem}.png"
    
    # infer size from the SVG itself
    svg2png(
        bytestring=svg_data,
        write_to=str(png_file),
        scale=1.0
    )
    print(f"Converted {svg_file.name} -> {png_file.name}")