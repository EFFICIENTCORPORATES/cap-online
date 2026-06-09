from PyPDF2 import PdfReader, PdfWriter

pdf = r"C:\Users\Efficient Corporates\Downloads\0_ICAI_CA_INTER_ADV_ACCOUNT (1).pdf"
reader = PdfReader(pdf)
total = len(reader.pages)

print(f"Total pages = {total}")

while True:
    s = int(input("Start page: "))
    e = int(input("End page: "))

    if e > total:
        print("End page exceeds total pages. Stopping.")
        break

    writer = PdfWriter()

    for i in range(s - 1, e):
        writer.add_page(reader.pages[i])

    out = f"split_{s}_{e}.pdf"

    with open(out, "wb") as f:
        writer.write(f)

    print(f"Saved: {out}")