from PIL import Image
from pathlib import Path

png_folder = Path("/Users/gboa/cluas/src/characters/avatars")
resized_folder = Path("/Users/gboa/cluas/src/characters/avatars")
resized_folder.mkdir(exist_ok=True)

for png_file in png_folder.glob("*.png"):
    img = Image.open(png_file)
    img = img.resize((512, 512), Image.LANCZOS)  # maintain quality
    img.save(resized_folder / png_file.name)
    print(f"Resized {png_file.name} -> {png_file.name}")