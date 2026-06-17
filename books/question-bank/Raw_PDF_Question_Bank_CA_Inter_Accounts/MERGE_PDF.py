from pathlib import Path
from pypdf import PdfReader, PdfWriter

# Get the folder where this script is located
current_folder = Path(__file__).resolve().parent

# Output file name
output_filename = "merged_output.pdf"

# Find only PDF files in the current folder (exclude output file)
pdf_files = sorted(
    [
        file for file in current_folder.iterdir()
        if file.is_file()
        and file.suffix.lower() == ".pdf"
        and file.name != output_filename
    ]
)

if not pdf_files:
    print("No PDF files found in the current folder.")
    raise SystemExit

writer = PdfWriter()

for pdf in pdf_files:
    print(f"Adding: {pdf.name}")

    reader = PdfReader(str(pdf))

    for page in reader.pages:
        writer.add_page(page)

output_path = current_folder / output_filename

with open(output_path, "wb") as output_file:
    writer.write(output_file)

print(f"\nSuccessfully merged {len(pdf_files)} PDFs.")
print(f"Output saved to: {output_path}")