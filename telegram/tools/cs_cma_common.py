"""
Shared metadata + parsing helpers for the CS/CMA ToC-extraction pipeline.
See _claude/skills/SKILL-cs-cma-toc-pipeline.md for the full writeup of why
this exists and how it works.

Unlike the CA Study Hub pipeline, CS and CMA study material ships as one
consolidated PDF per subject (all chapters in one file, no per-chapter
PDFs from the institute) -- so instead of verifying ICAI's own filenames,
this pipeline has to *derive* chapter boundaries from each PDF's own
printed Table of Contents, then reverse-engineer which actual PDF page
each printed page number corresponds to (the two are offset by however
many un-numbered/roman-numeral front-matter pages precede page "1").

Every (Course, Level, PaperNo, Subject) tuple below was read directly off
that file's own cover page (ICMAI: "FINAL / Paper 18 / Corporate Financial
Reporting" style; ICSI: "(i) / TITLE / GROUP N / PAPER N / EXECUTIVE
PROGRAMME" style) -- not guessed from the filename.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_ROOT = REPO_ROOT / "telegram" / "assets"

# folder name -> (Course, Level)
FOLDER_META = {
    "CS Exce": ("CS", "Executive"),
    "CS Prof": ("CS", "Professional"),
    "CS EET": ("CS", "CSEET"),
    "CMA Final": ("CMA", "Final"),
    "CMA Found Study mat": ("CMA", "Foundation"),
    "CMA Inter Study Mat": ("CMA", "Intermediate"),
}

# (folder, filename) -> (Group/Section label or None, PaperNo, Subject full name)
# Read from each file's own cover page -- see SKILL-cs-cma-toc-pipeline.md §2.
FILE_META = {
    # --- CS Executive (7 papers, Groups 1-2) ---
    ("CS Exce", "JI&GL Book with cover 17-2-2024.pdf"): ("Group 1", "1", "Jurisprudence, Interpretation & General Laws"),
    ("CS Exce", "Book - Company Law & Practices.pdf"): ("Group 1", "2", "Company Law & Practice"),
    ("CS Exce", "Setting Up of Business, Industrial & Labour Laws Book.pdf"): ("Group 1", "3", "Setting Up of Business, Industrial & Labour Laws"),
    ("CS Exce", "Final CA&FM Book 16-2-2024.pdf"): ("Group 1", "4", "Corporate Accounting & Financial Management"),
    ("CS Exce", "Final CM&SL Book 16-2-2024.pdf"): ("Group 2", "5", "Capital Market & Securities Laws"),
    ("CS Exce", "Final EC&IPL Book.pdf"): ("Group 2", "6", "Economic, Commercial & Intellectual Property Laws"),
    ("CS Exce", "Tax Law Book FInal 16-2-2024.pdf"): ("Group 2", "7", "Tax Laws & Practice"),

    # --- CS Professional (9 papers incl. electives, Groups 1-2) ---
    ("CS Prof", "ENVIRONMENTAL_SOCIAL_AND_GOVERNANCE_ESG_PRINCIPLES_PRACTICE_14082025.pdf"): ("Group 1", "1", "Environmental, Social and Governance (ESG) – Principles & Practice"),
    ("CS Prof", "Drafting_Pleadings_Appearances_Professional_Programme_July2023.pdf"): ("Group 1", "2", "Drafting, Pleadings & Appearances"),
    ("CS Prof", "Compliance_Management_Audit_Due_Diligence.pdf"): ("Group 1", "3", "Compliance Management, Audit & Due Diligence"),
    ("CS Prof", "CSR_Social_Governance.pdf"): ("Group 1", "4.1", "CSR & Social Governance"),
    ("CS Prof", "Internal_and_Forensic_Audit.pdf"): ("Group 1", "4.2", "Internal & Forensic Audit"),
    ("CS Prof", "Intellectual_Property_Rights_Law_Practice.pdf"): ("Group 1", "4.3", "Intellectual Property Rights – Law & Practice"),
    ("CS Prof", "Artificial_Intelligence_Data_Analytics_And_Cyber_Security_Laws_&_Practice.pdf"): ("Group 1", "4.4", "Artificial Intelligence, Data Analytics and Cyber Security – Laws & Practice"),
    ("CS Prof", "Book_Advanced_Direct_Laws&Practice_552025.pdf"): ("Group 1", "4.5", "Advanced Direct Tax Laws & Practice"),
    ("CS Prof", "Final_Book_IFSCA_Regulations_Listing_and_Compliances_20012026.pdf"): ("Group 1", "4.6", "IFSCA - Regulations, Listing and Compliances"),
    ("CS Prof", "SM_CF_Final_PP_14082025.pdf"): ("Group 2", "5", "Strategic Management & Corporate Finance"),
    ("CS Prof", "Corporate_Restruucturing_Valuation_Insolvency_14082025.pdf"): ("Group 2", "6", "Corporate Restructuring, Valuation & Insolvency"),
    ("CS Prof", "Arbitration_Mediation_Conciliation_Professional_Programme_July2023.pdf"): ("Group 2", "7.1", "Arbitration, Mediation & Conciliation"),
    ("CS Prof", "Final_Book_GST_&_Corporate_Tax_Planning_20_6_2025.pdf"): ("Group 2", "7.2", "Goods and Services Tax (GST) & Corporate Tax Planning"),
    ("CS Prof", "LLP_Final_PP.pdf"): ("Group 2", "7.3", "Labour Laws & Practice"),
    ("CS Prof", "Banking_&_Insurance_Law_Final.pdf"): ("Group 2", "7.4", "Banking & Insurance – Laws & Practice"),
    ("CS Prof", "Insolvency_and_Bankruptcy_Law_Practice1_14082025.pdf"): ("Group 2", "7.5", "Insolvency and Bankruptcy - Law & Practice"),

    # --- CS EET (4 papers, no Group) ---
    ("CS EET", "Paper_1_Business_Communication_CSEET_18122025.pdf"): (None, "1", "Business Communication"),
    ("CS EET", "Paper_2_Fundamental_of_Accounting_CSEET_18122025.pdf"): (None, "2", "Fundamentals of Accounting"),
    ("CS EET", "Paper_3_Economic_and_Business_Environment_CSEET_18122025.pdf"): (None, "3", "Economic and Business Environment"),
    ("CS EET", "Paper_4_Business_Law_&_Management_CSEET_18122025.pdf"): (None, "4", "Business Laws & Management"),

    # --- CMA Final (10 papers incl. 3 electives) ---
    ("CMA Final", "Corporate and Economic Law.pdf"): (None, "13", "Corporate and Economic Laws"),
    ("CMA Final", "SFM.pdf"): (None, "14", "Strategic Financial Management"),
    ("CMA Final", "Direct and Intl Tax.pdf"): (None, "15", "Direct Tax Laws and International Taxation"),
    ("CMA Final", "SCM.pdf"): (None, "16", "Strategic Cost Management"),
    ("CMA Final", "Cost and Mgmt Audit.pdf"): (None, "17", "Cost and Management Audit"),
    ("CMA Final", "FR.pdf"): (None, "18", "Corporate Financial Reporting"),
    ("CMA Final", "IDT.pdf"): (None, "19", "Indirect Tax Laws and Practice"),
    ("CMA Final", "SPM.pdf"): (None, "20A", "Strategic Performance Management and Business Valuation"),
    ("CMA Final", "Risk mgmt.pdf"): (None, "20B", "Risk Management in Banking and Insurance"),
    ("CMA Final", "Startup.pdf"): (None, "20C", "Entrepreneurship and Startup"),

    # --- CMA Foundation (4 papers) ---
    ("CMA Found Study mat", "CMA Foundation Fundamentals of business law and communication.pdf"): (None, "1", "Fundamentals of Business Laws and Business Communication"),
    ("CMA Found Study mat", "CMA Foundation Fundamentals of Financial and cost Accounting.pdf"): (None, "2", "Fundamentals of Financial and Cost Accounting"),
    ("CMA Found Study mat", "Fundamentals of Business mathmetics and stat.pdf"): (None, "3", "Fundamentals of Business Mathematics and Statistics"),
    ("CMA Found Study mat", "CMA Foundation Fundamentals of Business Economics and Mgmt.pdf"): (None, "4", "Fundamentals of Business Economics and Management"),

    # --- CMA Intermediate (9 files / 8 papers -- Paper 7 "Taxation" is one
    # paper split into two study-note volumes by ICMAI itself: Direct and
    # Indirect. Both really are "Paper 7" -- kept distinct via 7A/7B so
    # they don't collide, same pattern as CA Inter's Paper 3A/3B split. ---
    ("CMA Inter Study Mat", "Business Law and ethics.pdf"): (None, "5", "Business Laws and Ethics"),
    ("CMA Inter Study Mat", "Financial Accounting.pdf"): (None, "6", "Financial Accounting"),
    ("CMA Inter Study Mat", "Direct Tax.pdf"): (None, "7A", "Direct Taxation"),
    ("CMA Inter Study Mat", "Indirect Tax.pdf"): (None, "7B", "Indirect Taxation"),
    ("CMA Inter Study Mat", "Cost Accounting.pdf"): (None, "8", "Cost Accounting"),
    ("CMA Inter Study Mat", "OM SM.pdf"): (None, "9", "Operations Management and Strategic Management"),
    ("CMA Inter Study Mat", "Corporate Accounting.pdf"): (None, "10", "Corporate Accounting and Auditing"),
    ("CMA Inter Study Mat", "Financial Management.pdf"): (None, "11", "Financial Management and Business Data Analytics"),
    ("CMA Inter Study Mat", "Management Accounting.pdf"): (None, "12", "Management Accounting"),
}


def get_file_meta(folder: str, filename: str):
    course, level = FOLDER_META[folder]
    group, paper_no, subject = FILE_META[(folder, filename)]
    return {
        "Course": course,
        "Level": level,
        "Group": group,
        "PaperNo": paper_no,
        "Subject": subject,
    }


def publisher_of(folder: str) -> str:
    """'icmai' or 'icsi' -- determines which ToC parser to use."""
    return "icmai" if folder.startswith("CMA") else "icsi"


def all_source_files():
    for folder in FOLDER_META:
        d = ASSETS_ROOT / folder
        for pdf_path in sorted(d.glob("*.pdf")):
            key = (folder, pdf_path.name)
            if key not in FILE_META:
                raise KeyError(f"No FILE_META entry for {key} -- add one before running the pipeline.")
            yield folder, pdf_path


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()
