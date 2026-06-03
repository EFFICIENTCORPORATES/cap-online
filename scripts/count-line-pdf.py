from pypdf import PdfReader

reader = PdfReader("ICAI STUDY MATERIAL MODULE 2.pdf")

total_lines = 0

for page in reader.pages:
    text = page.extract_text()
    
    if text:
        total_lines += len(text.splitlines())

print("Total lines:", total_lines)