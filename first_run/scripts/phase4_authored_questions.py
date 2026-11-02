"""
phase4_authored_questions.py
=============================
Questions written from the ICAI study material to top up the Phase 4 tests that
fall short of 50 marks because the real MTP/RTP/PYQ pool is too small.

Every fact and figure in an answer is taken from, or computed from, the
chapter text in books/ca-inter/concept-book/raw_icai_study_materials/ -
nothing is added from outside it. Numerical cases use figures chosen here
(not copied from a past paper); every worked answer is re-derived in
verify_phase4_authored.py.

Each row matches the shape build_second_phase_tests.py renders.
"""


def _d(key, marks, q, a, topic):
    return {
        "key": key, "question_html": q, "answer_html": a, "marks": marks,
        "case_facts_html": None, "topics": None, "examiner_comment": None,
        "source_kind": "study_material", "estimated_marks": False,
        "study_source_label": "ICAI Study Material", "authored": True,
        "topic_text": topic,
    }


APPLICABILITY = [
    _d("APP-1", 12,
       "<p>(a) Explain the criteria under which a non-company entity is classified as a Micro, Small and Medium Sized Entity (MSME) for the applicability of Accounting Standards, as per the revised scheme effective from accounting periods commencing on or after 1st April, 2024. (5 Marks)</p>"
       "<p>(b) Om Finserv LLP had a turnover (excluding other income) of ₹180 crore and borrowings of ₹55 crore in FY 2023-24. It is not a listed entity, not a financial institution and not a subsidiary of any entity. Can it be classified as an MSME for FY 2024-25? (3 Marks)</p>"
       "<p>(c) Ravi Traders, an unlisted partnership firm, had a turnover (excluding other income) of ₹230 crore and borrowings of ₹45 crore in FY 2023-24. It is not a bank, financial institution or insurance company and is not a holding or subsidiary of any entity. Can it classify as an MSME for FY 2024-25? (4 Marks) (12 Marks)</p>",
       "<p><strong>(a)</strong> A non-company entity is an MSME only if <em>all</em> the following conditions are satisfied:</p>"
       "<ol><li>its equity or debt securities are not listed, or in the process of listing, on any stock exchange in India or outside India;</li>"
       "<li>it is not a bank, financial institution or an insurance company;</li>"
       "<li>its turnover (excluding other income) did not exceed ₹250 crore in the immediately preceding accounting year;</li>"
       "<li>it did not have borrowings in excess of ₹50 crore at any time during the immediately preceding accounting year; and</li>"
       "<li>it is not a holding or subsidiary of an entity which is not itself an MSME.</li></ol>"
       "<p>The conditions are tested as at the end of the relevant accounting period. A non-company entity that is not an MSME is a <strong>Large entity</strong> and must comply in full with all the Accounting Standards; MSMEs get the exemptions and relaxations in Annexure 1.</p>"
       "<p><strong>(b)</strong> Turnover of ₹180 crore is within the ₹250 crore limit, and the entity is unlisted, not a financial institution and not a subsidiary. However, its borrowings of ₹55 crore exceed the limit of ₹50 crore. One of the conditions fails, so Om Finserv LLP <strong>cannot</strong> be classified as an MSME. It is a Large entity and must comply with all the Accounting Standards in full, with no MSME exemptions.</p>"
       "<p><strong>(c)</strong> Turnover of ₹230 crore does not exceed ₹250 crore; borrowings of ₹45 crore do not exceed ₹50 crore; the firm is unlisted, is not a bank, financial institution or insurance company, and is neither a holding nor a subsidiary. Every condition is satisfied on the preceding-year figures, so Ravi Traders <strong>qualifies as an MSME</strong> for FY 2024-25 and may avail the exemptions and relaxations. If it avails them, it must disclose by way of a note that it is an MSME and has complied with the Accounting Standards insofar as they are applicable to an MSME.</p>",
       "Applicability of Accounting Standards - MSME classification"),
    _d("APP-2", 10,
       "<p>Which Accounting Standards are not applicable to MSMEs (non-company entities) in their entirety? State the conditions under which AS 18 and AS 28 are also not applicable, and explain the position of AS 14, AS 21, AS 23, AS 25 and AS 27 for such entities. (10 Marks)</p>",
       "<p><strong>1. Not applicable to any MSME in their entirety:</strong> AS 3 (Cash Flow Statements), AS 17 (Segment Reporting), AS 20 (Earnings per Share) and AS 24 (Discontinuing Operations).</p>"
       "<p><strong>2. AS 18 (Related Party Disclosures) and AS 28 (Impairment of Assets)</strong> are not applicable in their entirety to an MSME which satisfies all of the following:</p>"
       "<ul><li>its turnover (excluding other income) does not exceed ₹50 crore in the immediately preceding accounting year;</li>"
       "<li>it does not have borrowings in excess of ₹10 crore at any time during the immediately preceding accounting year; and</li>"
       "<li>it is not a holding or subsidiary of an MSME not covered by this exemption.</li></ul>"
       "<p>An MSME that is otherwise not exempted from AS 28 may measure 'value in use' on a reasonable estimate instead of the present value technique, and need not disclose the information required by paragraph 121(g).</p>"
       "<p><strong>3. AS 14 and AS 27:</strong> MSMEs generally have no transactions covered by AS 14 (Accounting for Amalgamations) or jointly controlled operations or assets under AS 27, so these standards are not applicable. However, if there are any such transactions, the entity must apply the requirements of the relevant standard.</p>"
       "<p><strong>4. AS 21, AS 23, AS 25 and AS 27 (consolidation part):</strong> a non-company entity is not required to present consolidated financial statements or an interim financial report. The relevant standard applies only if the entity is required to, or elects to, prepare and present consolidated financial statements or an interim financial report.</p>",
       "Applicability of Accounting Standards - exemptions for MSMEs"),
    _d("APP-3", 10,
       "<p>Explain the criteria for classification of companies for applicability of Accounting Standards. Which Accounting Standard is not applicable to Small and Medium-sized Companies (SMCs) in its entirety, and in respect of which standards have relaxations been given to SMCs? (10 Marks)</p>",
       "<p><strong>Classification.</strong> For companies there are two levels: Small and Medium-sized Companies (SMCs), as defined in the Companies (Accounting Standards) Rules, 2021, and companies other than SMCs (Non-SMCs). Non-SMCs must comply with all the Accounting Standards in their entirety; certain exemptions and relaxations are given to SMCs.</p>"
       "<p><strong>Not applicable to SMCs in its entirety:</strong> AS 17, Segment Reporting.</p>"
       "<p><strong>Relaxations for SMCs:</strong></p>"
       "<ul><li><strong>AS 15 (Employee Benefits):</strong> relaxation from recognition and measurement of short-term accumulating non-vesting compensated absences; from discounting of amounts falling due more than 12 months after the balance sheet date; and from the defined benefit plan and other long-term benefit provisions. However, the accrued liability must be actuarially determined using the Projected Unit Credit Method, with the discount rate based on market yields on government bonds at the balance sheet date (paragraph 78), and actuarial assumptions disclosed as per paragraph 120(l).</li>"
       "<li><strong>AS 19 (Leases):</strong> certain disclosure paragraphs (22(c), (e), (f); 25(a), (b), (e); 37(a), (f); 46(b), (d)) are not applicable.</li>"
       "<li><strong>AS 20 (Earnings Per Share):</strong> disclosure of diluted EPS (both including and excluding extraordinary items) is exempted.</li>"
       "<li><strong>AS 28 (Impairment of Assets):</strong> 'value in use' may be measured on a reasonable estimate instead of the present value technique; the discount rate provisions do not apply and the information in paragraph 121(g) need not be disclosed.</li>"
       "<li><strong>AS 29 (Provisions, Contingent Liabilities and Contingent Assets):</strong> disclosure paragraphs 66 and 67 are not applicable.</li></ul>"
       "<p><strong>AS 25 (Interim Financial Reporting)</strong> does not require a company to present an interim financial report; it applies only if the company is required or elects to present one (for example, quarterly results required by SEBI from certain Non-SMCs).</p>",
       "Applicability of Accounting Standards - companies"),
    _d("APP-4", 10,
       "<p>(a) What additional requirements apply to an MSME that avails exemptions or relaxations under the Accounting Standards? (4 Marks)</p>"
       "<p>(b) ABC &amp; Co., a non-company entity, was an MSME in FY 2022-23 and availed certain exemptions. In FY 2023-24 its turnover exceeded ₹300 crore, so it ceased to be an MSME. State how ABC &amp; Co. should deal with the Accounting Standards in FY 2024-25 and the disclosures it must make. (3 Marks)</p>"
       "<p>(c) MNO Enterprises, an unlisted LLP, qualifies as an MSME. It chooses not to avail the relaxation from AS 15 (Employee Benefits) but avails the exemption from AS 3. What disclosure is required? Also state when an entity that was earlier not an MSME and later becomes one can start availing MSME exemptions. (3 Marks) (10 Marks)</p>",
       "<p><strong>(a)</strong> An MSME that avails the exemptions or relaxations must disclose, by way of a note to its financial statements, the fact that it is an MSME and has complied with the Accounting Standards insofar as they are applicable to an MSME. If it opts not to avail the exemptions in respect of some, but not all, Standards, it must disclose the Standard(s) in respect of which it has availed the exemption or relaxation. If it opts not to avail an exemption, it must comply with the relevant requirements of that Standard. Partial exemption or relaxation must not be permitted to mislead the users of financial statements.</p>"
       "<p><strong>(b)</strong> Where an MSME no longer qualifies, the relevant Standards or requirements become applicable from the current period. So ABC &amp; Co. must apply the full Accounting Standards in FY 2024-25. The corresponding previous-period figures need not be revised merely because it ceased to be an MSME. It must disclose in the notes that it was an MSME in the previous period and had availed the exemptions or relaxations, and that the previous-period figures have not been revised.</p>"
       "<p><strong>(c)</strong> MNO Enterprises must disclose, by way of a note, that it is an MSME, and mention the Standard in respect of which it has availed the exemption (AS 3), since it has not availed it for all Standards. It need not revise any previous-year figures. An entity that was previously not an MSME and subsequently becomes one cannot claim MSME exemptions or relaxations until it remains an MSME for two consecutive years.</p>",
       "Applicability of Accounting Standards - additional requirements and disclosures"),
]

# Verbatim ICAI Test Your Knowledge MCQs for Applicability (the study-material
# parser cannot read this chapter's number-then-letter answer layout). Answers
# are the ICAI key printed under ANSWERS/HINTS: 1 (b) 2 (c) 3 (b) 4 (c) 5 (d)
# 6 (c) 7 (b) 8 (c) - the six below are TYK Q1, Q2, Q3, Q4, Q7, Q8.
APPLICABILITY_MCQS = [
    ("From which accounting period is the revised scheme for applicability of Accounting Standards to non-company entities effective?",
     {"A": "April 1, 2023", "B": "April 1, 2024", "C": "August 13, 2024", "D": "April 1, 2025"}, "B", 1),
    ("Which of the following is not a condition for classification of a non-company entity as an MSME under the revised ICAI criteria?",
     {"A": "Turnover should not exceed ₹250 crore", "B": "Entity should not be a bank or insurance company",
      "C": "Entity should not have borrowings exceeding ₹100 crore", "D": "Entity should not be a subsidiary of a non-MSME"}, "C", 2),
    ("Which of the following Accounting Standards is not applicable in its entirety to all MSMEs?",
     {"A": "AS 1 - Disclosure of Accounting Policies", "B": "AS 3 - Cash Flow Statements",
      "C": "AS 9 - Revenue Recognition", "D": "AS 22 - Accounting for Taxes on Income"}, "B", 3),
    ("If a non-company entity newly qualifies as an MSME, when can it start availing exemptions available to MSMEs?",
     {"A": "Immediately from the first year of qualification", "B": "From the second year after qualification",
      "C": "Only when it remains as an MSME for two consecutive years", "D": "Never; exemptions are only for companies"}, "C", 4),
    ("Zeta Traders, a partnership firm, had a turnover of ₹240 crore and borrowings of ₹40 crore in FY 2023-24. It is not a bank, not into insurance business or listed entity and also not a holding or subsidiary of any other entity. For FY 2024-25, it wants to avail exemptions available to MSMEs under Accounting Standards. Is it eligible?",
     {"A": "Yes, because both turnover and borrowing are within limits", "B": "No, because it had high turnover",
      "C": "No, because it must remain MSME for two years to claim exemptions", "D": "Yes, because it qualifies as an MSME this year"}, "D", 5),
    ("ABC & Co., a non-company entity, was an MSME in FY 2022-23 and availed certain exemptions. In FY 2023-24, its turnover exceeded ₹300 crore. What should ABC & Co. do in FY 2024-25?",
     {"A": "Continue to use all MSME exemptions", "B": "Revise prior year financials to remove MSME exemptions",
      "C": "Apply full AS requirements in FY 2024-25 and disclose change", "D": "Continue partial compliance with disclosure only"}, "C", 6),
    ("X Ltd., a listed non-company entity, has turnover of ₹40 crore and borrowings of ₹5 crore. It is not a bank or a financial institution. Can it be classified as an MSME?",
     {"A": "Yes, because turnover and borrowings are within MSME limits", "B": "No, because it is a listed entity",
      "C": "Yes, because it is not a subsidiary or holding company", "D": "No, because listed entities are classified as large entities"}, "B", 7),
    ("MNO Enterprises, an unlisted LLP, qualifies as an MSME in FY 2023-24 and chooses to not claim exemption from AS 15 (Employee Benefits), but avails relaxation from AS 3. What disclosure is required in its financial statements?",
     {"A": "It must disclose full compliance with all AS", "B": "It need not disclose anything since partial exemption is allowed",
      "C": "It must disclose that it is an MSME and mention Standards from which exemptions are availed",
      "D": "It must revise previous year's financials due to partial compliance"}, "C", 8),
]

INTRO = [
    _d("INT-1", 10,
       "<p>Explain the standard-setting process followed by the Accounting Standards Board (ASB) of the ICAI. What is the role of the NFRA and the Ministry of Corporate Affairs in respect of Accounting Standards for companies? (10 Marks)</p>",
       "<p>The ASB, constituted by the ICAI in 1977, includes representatives of industry, associations of industry (ASSOCHAM, CII, FICCI), regulators, academicians and government departments. Though constituted by the Council of the ICAI, it is independent in formulating accounting standards. The steps are:</p>"
       "<ol><li><strong>Identification of area:</strong> the ASB identifies broad areas for which a standard is to be formulated.</li>"
       "<li><strong>Constitution of study groups:</strong> study groups prepare preliminary drafts (objective and scope, definitions, recognition and measurement principles, presentation and disclosure requirements); the ASB considers and, if needed, revises them.</li>"
       "<li><strong>Preparation of draft and its circulation:</strong> the revised draft is circulated to the Council members and specified outside bodies such as MCA, SEBI, C&amp;AG, CBDT and SCOPE for comments.</li>"
       "<li><strong>Ascertainment of views:</strong> meetings are held with representatives of the outside bodies to ascertain their views on the draft.</li>"
       "<li><strong>Finalisation of exposure draft (E.D.):</strong> the exposure draft is finalised and issued inviting public comments.</li>"
       "<li><strong>Comments on the exposure draft:</strong> the ASB considers the comments and finalises the draft standard for submission to the Council.</li>"
       "<li><strong>Modification of the draft:</strong> the Council considers the final draft and, if necessary, modifies it in consultation with the ASB.</li>"
       "<li><strong>Issue of the AS:</strong> the standard is issued by the ICAI (for non-corporate entities).</li></ol>"
       "<p><strong>Role of NFRA and MCA:</strong> for corporate entities, the standards are issued by the MCA in consultation with the NFRA. Under Section 133 of the Companies Act, 2013, the Central Government may prescribe standards of accounting as recommended by the ICAI, in consultation with and after examination of the recommendations of the NFRA. NFRA recommends the standards to the MCA, and the MCA specifies the standards applicable to companies.</p>",
       "Introduction to Accounting Standards - standard setting process"),
    _d("INT-2", 9,
       "<p>(a) Distinguish between 'adoption' and 'convergence' as techniques of becoming IFRS compliant. (3 Marks)</p>"
       "<p>(b) India decided to converge with, and not adopt, IFRS. Explain what 'carve-outs' and 'carve-ins' in Ind AS mean and the factors on account of which Ind AS depart from IFRS. (4 Marks)</p>"
       "<p>(c) State any four benefits of convergence with IFRS. (2 Marks) (9 Marks)</p>",
       "<p><strong>(a)</strong> <em>Adoption:</em> the country sets a specific timetable when specific entities are required to use IFRS as issued by the IASB. <em>Convergence:</em> the country develops high-quality, compatible accounting standards and aligns its standards with those of other standard setters with a certain rate of compromise, by adopting the requirements of the standards either fully or partially. Ind AS are almost similar to IFRS but with a few carve-outs to suit the Indian environment.</p>"
       "<p><strong>(b)</strong> India converged after a detailed analysis of the IFRS requirements and extensive discussion with stakeholders; Ind AS are kept as close to the corresponding IAS/IFRS as possible, with departures only where absolutely essential, on account of:</p>"
       "<ul><li><strong>Terminology differences</strong> - to align with law, e.g. 'statement of profit and loss' instead of 'statement of comprehensive income' and 'balance sheet' instead of 'statement of financial position';</li>"
       "<li><strong>Removal of options</strong> in accounting principles and practices, for consistency and comparability (these do not result in carve-outs);</li>"
       "<li><strong>Differences in the economic environment</strong> of India compared with that assumed by IFRS.</li></ul>"
       "<p>Departures from the accounting principles and practices in IFRS arising from differences in economic conditions are known as <strong>carve-outs</strong>. Additional guidance given in Ind AS over and above IFRS is a <strong>carve-in</strong>.</p>"
       "<p><strong>(c)</strong> Benefits of convergence: (i) improves investor confidence across the world through transparency and comparability; (ii) improves inter-unit, inter-firm and inter-industry comparison; (iii) group consolidation is easier when all group companies use the same standard irrespective of location; (iv) financial statements are acceptable to stock exchanges across the globe, facilitating listing of Indian companies on international exchanges.</p>",
       "Introduction to Accounting Standards - IFRS, convergence and Ind AS"),
    _d("INT-3", 10,
       "<p>(a) How many Accounting Standards are effectively in force in India at present? State which standards have been withdrawn and why. (4 Marks)</p>"
       "<p>(b) Discuss the status of Accounting Standards in India: can they override law, and when are they mandatory? (3 Marks)</p>"
       "<p>(c) Name the Accounting Standards that were revised to bring them in line with the corresponding Ind AS under the Companies (Accounting Standards) Rules, 2021. (3 Marks) (10 Marks)</p>",
       "<p><strong>(a)</strong> There are effectively <strong>27</strong> Accounting Standards at present. AS 6 on 'Depreciation Accounting' was withdrawn on the revision of AS 10 'Property, Plant and Equipment' (earlier AS 10 was 'Accounting for Fixed Assets'), and AS 8 on 'Accounting for Research and Development' was withdrawn consequent to the issuance of AS 26 'Intangible Assets'. The Companies Act had earlier notified 28 standards; in 2016 the MCA withdrew AS 6, leaving 27 notified standards under the Companies (Accounting Standards) Rules, 2021.</p>"
       "<p><strong>(b)</strong> The standards are developed by the ASB of the ICAI. The Institute is not a legislative body and can enforce compliance with its standards only by its members. The standards cannot override laws and local regulations; where there is conflict, the statute prevails. They are nevertheless made mandatory from the dates specified, and are generally applicable to all enterprises subject to certain exceptions. The implication of mandatory status depends on whether the statute governing the enterprise requires compliance with them; for companies, the MCA has notified them under the Companies Act, and the Rules of 2021 apply to accounting periods beginning on or after 1st April, 2021.</p>"
       "<p><strong>(c)</strong> AS 2, AS 4, AS 10, AS 13, AS 14, AS 21 and AS 29 were revised to make them in line with the corresponding Ind AS to the extent possible.</p>",
       "Introduction to Accounting Standards - number and status of standards"),
]

AS01 = [
    _d("AS1-1", 5,
       "<p>Rangoli Traders purchased 800 units of an article at ₹25 per unit and sold 600 units at ₹40 per unit during the year. Compute the profit for the year if the net realisable value per unit of the unsold stock is (i) ₹32 and (ii) ₹20. Explain how the principle of prudence is reflected in your treatment. (5 Marks)</p>",
       "<p>Sales = 600 × ₹40 = ₹24,000; Purchases = 800 × ₹25 = ₹20,000. Closing stock is valued at the lower of cost and net realisable value.</p>"
       "<table border='1' cellpadding='4'><tr><th>Particulars</th><th>(i) NRV ₹32</th><th>(ii) NRV ₹20</th></tr>"
       "<tr><td>Sales</td><td>24,000</td><td>24,000</td></tr>"
       "<tr><td>Closing stock (200 units)</td><td>5,000 (at cost ₹25)</td><td>4,000 (at NRV ₹20)</td></tr>"
       "<tr><td>Cost of goods sold (20,000 - closing stock)</td><td>15,000</td><td>16,000</td></tr>"
       "<tr><td><strong>Profit</strong></td><td><strong>9,000</strong></td><td><strong>8,000</strong></td></tr></table>"
       "<p><strong>Prudence:</strong> in case (i) the expected profit of 200 × (₹32 - ₹25) = ₹1,400 on the unsold units is not anticipated; stock stays at cost. In case (ii) the expected loss of 200 × (₹25 - ₹20) = ₹1,000 is recognised by valuing stock at NRV. Profits are not anticipated but losses are provided for.</p>",
       "AS 1 - Prudence in selection of accounting policies"),
    _d("AS1-2", 7,
       "<p>Zenith Ltd. valued its inventory on FIFO basis up to last year. In the current year it changed to the weighted average method, which better reflects the consumption pattern of inventory. The closing inventory is ₹5,00,000 under FIFO and ₹4,60,000 under the weighted average method; net realisable value of every item exceeds its cost. Explain, as per AS 1, how the change should be disclosed, and the effect on profit and inventory. State also the position if a change has no material effect in the current period. (7 Marks)</p>",
       "<p><strong>Effect:</strong> closing inventory falls from ₹5,00,000 to ₹4,60,000, a reduction of ₹40,000; profit for the year is therefore also reduced by ₹40,000.</p>"
       "<p><strong>Disclosure:</strong> as per AS 1, any change in accounting policy which has a material effect in the current period, or is reasonably expected to have a material effect in a later period, should be disclosed. Where the change has a material effect in the current period, the amount by which any item in the financial statements is affected should also be disclosed to the extent ascertainable; where it is not ascertainable wholly or in part, that fact should be indicated. A bare statement that a policy has changed is of little use to a reader, so the effect should be given. A suitable note: <em>'The company values its inventory at lower of cost or net realisable value. In the present year the company has changed to the weighted average method, which better reflects the consumption pattern of inventory, for ascertaining inventory costs from the earlier practice of using FIFO. The change in policy has reduced profit for the year and value of inventory as at the year end by ₹40,000.'</em></p>"
       "<p><strong>No material effect in the current period:</strong> if the change is reasonably expected to have a material effect in future periods, it must still be disclosed in the current period, even though it has no material effect now. This ensures that all important changes in accounting policies are actually disclosed.</p>",
       "AS 1 - Disclosure of changes in accounting policies"),
    _d("AS1-3", 10,
       "<p>Write short notes, with examples, on: (a) Prudence as a consideration in the selection of accounting policies; and (b) Materiality, including the quantitative limits prescribed in Schedule III to the Companies Act, 2013. (5 + 5 = 10 Marks)</p>",
       "<p><strong>(a) Prudence.</strong> Because of uncertainty about future events, profits are not anticipated but losses are provided for as a matter of conservatism. Provision should be made for all known liabilities and losses even though the amount cannot be determined with certainty and is only a best estimate on the information available. Exercising prudence ensures that (i) profits are not overstated, (ii) losses are not understated, (iii) assets are not overstated and (iv) liabilities are not understated. The common example is valuing inventory at the lower of cost and net realisable value. Prudence does not permit creation of hidden reserves by understating profits and assets or overstating liabilities and losses; for instance, for a pending damages suit no provision is charged to profit unless the probability of losing the suit is greater than the probability of not losing it.</p>"
       "<p><strong>(b) Materiality.</strong> Financial statements should disclose all material items, i.e. items the knowledge of which might influence the decisions of the user. Materiality is not always a matter of relative size: for example, a small amount lost through fraud by certain employees may indicate a serious flaw in internal control that needs immediate attention. In certain cases quantitative limits are specified. Under Schedule III, a company should disclose by way of notes additional information on any item of income or expenditure which exceeds 1% of the revenue from operations or ₹1,00,000, whichever is higher; and should disclose in the Notes to Accounts the shares held by each shareholder holding more than 5% of the shares, specifying the number of shares held.</p>",
       "AS 1 - Prudence and materiality"),
]

AS17 = [
    _d("AS17-1", 10,
       "<p>The Chief Accountant of Delta Ltd. provides the following data about its five segments (₹ in lakhs). Revenue includes inter-segment revenue of ₹50 lakhs in Segment A and ₹10 lakhs in Segment B.</p>"
       "<table border='1' cellpadding='4'><tr><th>Particulars</th><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th><th>Total</th></tr>"
       "<tr><td>Segment revenue</td><td>450</td><td>260</td><td>150</td><td>70</td><td>70</td><td>1,000</td></tr>"
       "<tr><td>Segment result</td><td>70</td><td>(30)</td><td>20</td><td>6</td><td>(4)</td><td>62</td></tr>"
       "<tr><td>Segment assets</td><td>320</td><td>190</td><td>110</td><td>45</td><td>35</td><td>700</td></tr></table>"
       "<p>(a) Identify the reportable segments by applying the 10% tests laid down in AS 17. (7 Marks)</p>"
       "<p>(b) Apply the 75% test and state whether any additional segment must be reported. (3 Marks) (10 Marks)</p>",
       "<p><strong>(a) 10% tests</strong> (a segment is reportable if it meets any one test):</p>"
       "<p><em>Revenue test:</em> 10% of total revenue (external + internal) of ₹1,000 lakhs = ₹100 lakhs. A (450), B (260) and C (150) meet it; D (70) and E (70) do not.</p>"
       "<p><em>Result test:</em> profit of profitable segments = 70 + 20 + 6 = ₹96 lakhs; loss of loss-making segments = 30 + 4 = ₹34 lakhs. The greater in absolute amount is ₹96 lakhs; 10% = ₹9.6 lakhs. A (70), B (30) and C (20) meet it; D (6) and E (4) do not.</p>"
       "<p><em>Asset test:</em> 10% of total segment assets of ₹700 lakhs = ₹70 lakhs. A (320), B (190) and C (110) meet it; D (45) and E (35) do not.</p>"
       "<p>Segments <strong>A, B and C are reportable</strong>. D and E meet none of the tests; they may be designated reportable at the discretion of management, otherwise they form part of the unallocated reconciling item.</p>"
       "<p><strong>(b) 75% test:</strong> total enterprise revenue (external) = 1,000 - inter-segment 60 = ₹940 lakhs. External revenue of the reportable segments = A (450 - 50) + B (260 - 10) + C 150 = 400 + 250 + 150 = ₹800 lakhs. 800 / 940 = 85.1%, which is not less than 75%. No additional segment needs to be identified as reportable.</p>",
       "AS 17 - Identification of reportable segments"),
    _d("AS17-2", 8,
       "<p>(a) Distinguish between the primary and secondary segment reporting formats under AS 17. (3 Marks)</p>"
       "<p>(b) List the disclosures required for each reportable segment under the primary reporting format, and the reconciliations to be presented. (5 Marks) (8 Marks)</p>",
       "<p><strong>(a)</strong> The dominant source and nature of the risks and returns of an enterprise governs which is its primary format. If the risks and returns are affected predominantly by differences in the products and services it produces, the <strong>primary format is business segments</strong> and the secondary information is reported geographically. If they are affected predominantly by the fact that it operates in different countries or geographical areas, the <strong>primary format is geographical segments</strong> and the secondary information is reported for groups of related products and services. The primary format calls for the fuller disclosure; the secondary format calls for a smaller set (revenue from external customers, carrying amount of segment assets and cost incurred to acquire segment assets) for segments meeting the 10% thresholds.</p>"
       "<p><strong>(b)</strong> For each reportable segment under the primary format an enterprise should disclose: (i) segment revenue, classified into revenue from sales to external customers and revenue from transactions with other segments; (ii) segment result; (iii) total carrying amount of segment assets; (iv) total amount of segment liabilities; (v) total cost incurred during the period to acquire segment assets expected to be used for more than one period (tangible and intangible fixed assets); (vi) total expense included in the segment result for depreciation and amortisation of segment assets; and (vii) total amount of significant non-cash expenses, other than depreciation and amortisation, included in segment expense. An enterprise that reports cash flows from operating, investing and financing activities of a segment need not disclose (vi) and (vii).</p>"
       "<p>The enterprise should also present a reconciliation between the segment information and the aggregated information in the enterprise financial statements: segment revenue to enterprise revenue; segment result to enterprise net profit or loss; segment assets to enterprise assets; and segment liabilities to enterprise liabilities.</p>",
       "AS 17 - Primary and secondary reporting formats; disclosures"),
    _d("AS17-3", 9,
       "<p>Kiran Ltd. has a business segment 'Appliances' (not primarily of a financial nature). The following information is available (₹ in lakhs):</p>"
       "<ul><li>Sales to external customers 500; inter-segment sales (at the actual transfer price) 60; dividend income 10</li>"
       "<li>Expenses directly attributable to the segment 380; common expenses allocable on a reasonable basis 40</li>"
       "<li>Head-office administrative expenses 30; interest on bank loan 25; income tax expense 20; extraordinary loss 15</li>"
       "<li>Fixed assets used in the segment 600; inventories 150; trade receivables 120 (gross) with provision for doubtful debts of 20 shown as a direct offset in the balance sheet; head-office building 90; deferred tax asset 25</li></ul>"
       "<p>(a) Compute the segment revenue, segment expense and segment result. (6 Marks)</p>"
       "<p>(b) Compute the segment assets. (3 Marks) (9 Marks)</p>",
       "<p><strong>(a)</strong></p>"
       "<table border='1' cellpadding='4'><tr><th>Particulars</th><th>₹ lakhs</th></tr>"
       "<tr><td>Segment revenue: external 500 + inter-segment 60</td><td>560</td></tr>"
       "<tr><td>Segment expense: directly attributable 380 + allocable common 40</td><td>420</td></tr>"
       "<tr><td><strong>Segment result</strong> (560 - 420)</td><td><strong>140</strong></td></tr></table>"
       "<p>Segment revenue includes revenue from transactions with other segments, but excludes interest and dividend income (the segment is not primarily of a financial nature) and extraordinary items; so dividend income of ₹10 lakhs and the extraordinary loss are left out. Segment expense excludes extraordinary items, interest expense, income tax expense and general administrative / head-office expenses relating to the enterprise as a whole; so head-office expenses ₹30 lakhs, interest ₹25 lakhs, income tax ₹20 lakhs and the extraordinary loss ₹15 lakhs are not segment expenses.</p>"
       "<p><strong>(b)</strong> Segment assets are the operating assets employed by the segment, determined after deducting related provisions reported as direct offsets in the balance sheet, and exclude income tax assets and assets used for general enterprise or head-office purposes.</p>"
       "<table border='1' cellpadding='4'><tr><th>Particulars</th><th>₹ lakhs</th></tr>"
       "<tr><td>Fixed assets</td><td>600</td></tr><tr><td>Inventories</td><td>150</td></tr>"
       "<tr><td>Trade receivables (120 - 20 provision)</td><td>100</td></tr>"
       "<tr><td><strong>Segment assets</strong></td><td><strong>850</strong></td></tr></table>"
       "<p>The head-office building (₹90 lakhs) and the deferred tax asset (₹25 lakhs) are excluded.</p>",
       "AS 17 - Segment revenue, expense, result and assets"),
]

AUTHORED = {
    "applicability": APPLICABILITY,
    "intro-to-as": INTRO,
    "as01": AS01,
    "as17": AS17,
}
