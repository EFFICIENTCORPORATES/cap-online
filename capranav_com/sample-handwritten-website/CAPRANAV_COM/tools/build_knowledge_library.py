#!/usr/bin/env python3
"""Build the static CAPRANAV student knowledge catalogue from verified local sources."""
from pathlib import Path
import json, re

ROOT = Path(__file__).resolve().parents[1]
raw = (ROOT / "assets" / "notes-data.js").read_text(encoding="utf-8")
notes = json.loads(raw.split("=", 1)[1].strip().rstrip(";"))["notes"]

themes = {
"Daily Discipline": [
("Choose Discipline Before Regret","Preparation improves when the student accepts the small daily discomfort of focused work instead of postponing it until result-day regret."),
("Set the Three Non-Negotiable Priorities","Health, family responsibilities and the CA goal need an explicit order so daily decisions do not depend on mood."),
("Create a Study-Only Phone Space","Separate classes, notes, PDFs and useful AI tools from distracting social apps by using a second phone profile or strict app restrictions."),
("Use a Fixed Wake Anchor","A stable wake-up time protects the day’s first study block and reduces repeated negotiation with the alarm."),
("Protect Six to Eight Hours of Sleep","Sleep supports memory consolidation; cutting it to create artificial study hours usually reduces the quality of the following day."),
("Take the First Natural Wake-Up Window","Getting up at the first genuine wake-up often preserves freshness better than returning to fragmented sleep."),
("Move for Fifteen Minutes Every Day","Walking, stretching, yoga or sport restores physical energy that students often mistake for mental fatigue."),
("Apply the 20-20-20 Eye Rule","Every twenty minutes, looking twenty feet away for twenty seconds reduces strain during long screen-based study days."),
("Eat Light Before Deep-Study Blocks","Heavy meals can reduce alertness; lighter food and steady hydration are better companions to demanding learning."),
("Wear Blinders Against Comparison","Mute progress-comparison groups and measure preparation against your own targets, errors and weekly output."),
("Use the Two-Minute Park Protocol","Write a troubling thought on paper before studying so the mind can treat it as recorded and return to the immediate task."),
("End the Day with a Mental Flashback","Replaying the day before sleep strengthens recall and shows which concepts still feel incomplete."),
("Maintain a Private Voice-Note Diary","A short self-message records what worked, what failed and what must move into tomorrow’s plan."),
("Write Targets in Four Parts","A valid target states the chapter, activity, quantity and completion test; anything less remains a wish."),
("Measure Outputs, Not Chair-Time","Questions completed, concepts recalled and errors corrected reveal progress better than the number of hours spent sitting."),
("Run a Sunday Data Review","Review hours, chapters, questions and accuracy once a week, then adjust the next week using evidence rather than emotion."),
("Keep One Hobby Alive","A controlled hobby protects identity and recovery without allowing recreation to displace the week’s academic commitments."),
("Build a Personal Scoreboard","Track improvement against your previous week instead of copying somebody else’s pace or timetable."),
("Recover from a Broken Streak","Missing one habit does not justify abandoning the system; resume at the next available block without drama."),
("Use the Bucket 0 Daily Tick","A short nightly checklist turns sleep, movement, food, focus, targets and reflection into a repeatable operating system.")
],
"Foundation Strategy": [
("Build a 30-Day Foundation Battle Plan","Split the preparation period into concept-and-tool building followed by timed mock execution and correction."),
("Separate Descriptive and MCQ Papers","Accounts and Law require written presentation practice, while Quantitative Aptitude and Economics demand speed, elimination and accuracy."),
("Create Sanjeevani Booti 1: Concept Sheets","Compress each chapter into one page containing the concept in your own words, its source and the usual examination demand."),
("Create Sanjeevani Booti 2: Error Register","Record every wrong answer and every lucky correct answer, together with the reason and the replacement method."),
("Create Sanjeevani Booti 3: Visual Vault","Convert formulas, formats, provisions, penalties and time limits into quickly retrievable visual sheets."),
("Limit Every Chapter to One Revision Page","Compression forces selection; the final page should support recall, not reproduce the entire textbook."),
("Use ICAI RTPs Correctly","Attempt relevant questions before reading answers and mark every new adjustment, presentation requirement and recurring concept."),
("Turn MTPs into Full Exam Rehearsals","Write complete MTPs at the actual exam time with the correct duration, no pauses and immediate post-test analysis."),
("Use Five Years of PYQs in Two Passes","First solve past questions chapter-wise to build patterns, then solve full papers to practise selection and switching."),
("Set a Minimum MCQ Volume","Build breadth by completing a defined number of MCQs per chapter and revisiting all low-confidence correct responses."),
("Analyse a Mock on the Same Day","Classify each lost mark as concept, calculation, interpretation, presentation, time or guessing while the attempt is still fresh."),
("Use the 60 Percent Confidence Rule","In negatively marked papers, attempt after elimination when confidence is sufficient; avoid blind guessing."),
("Cap One MCQ at Ninety Seconds","Mark, skip and return when a question exceeds the time budget; decision speed must be trained during mocks."),
("Calculate Before Looking at Options","For quantitative MCQs, form the solution independently before using options, reducing reverse-engineering errors."),
("Prepare the Gap-Day Plan in Advance","Decide the exact notes, formats, errors and chapters for each examination gap before the examination cycle begins."),
("Revise the Error Register Before Every Mock","The register is useful only when it changes behaviour in the next attempt, not when it is completed after preparation ends."),
("Practise Accounts in Exam Format","Use headings, working notes and orderly presentation from the first serious question-practice session."),
("Revise Law Through Applicability","Connect provisions to the facts and conditions in which they apply instead of memorising isolated sentences."),
("Create a Formula Retrieval System","Store Quantitative Aptitude formulas by question type and trigger, then practise selecting the formula without prompts."),
("Protect the Final Morning","Use the last morning for planned recall sheets and recurring errors, not for starting an untouched source.")
],
"CA Inter Strategy": [
("Map the Advanced Accounting Syllabus","List every chapter, its conceptual weight, practice demand and current confidence before allocating time."),
("Use a Coverage-Practice-Revision Cycle","Do not wait for classes to end; attach same-day practice and scheduled retrieval to every completed concept."),
("Build Layer 1 for Complete Understanding","Use official ICAI material and full class notes to establish definitions, principles, conditions and complete illustrations."),
("Build Layer 2 for Chapter Revision","Convert complete learning into structured chapter summaries that preserve the decision logic and major adjustments."),
("Build Layer 3 for Final Retrieval","Reduce each chapter to one-liners, triggers, formats and personal errors for rapid examination-week revision."),
("Classify Every Error","Separate concept, interpretation, calculation and presentation errors because each requires a different correction."),
("Practise Mixed-Chapter Sets","Mixed questions train recognition and switching, preventing chapter-wise comfort from becoming false confidence."),
("Target 30 out of 30 in MCQs","Use daily topic sets, immediate feedback and an accuracy log to make the objective section a systematic scoring area."),
("Write Working Notes Before the Final Answer","A clear working-note structure reduces calculation errors and helps earn method marks even when the final figure differs."),
("Use Chapter Tests as Repair Points","Review the test in the next learning cycle and feed mistakes directly into the personal error register."),
("Use Cumulative ITD Tests","Full-syllabus or till-date tests reveal whether earlier chapters survive after new chapters are added."),
("Plan Two Full-Paper Mocks","Use the actual three-hour pattern, analyse question selection and repair the error log before the second paper."),
("Build a Doubt Resolution Pipeline","Capture doubts during practice, attempt a self-explanation, then use class, group or Zoom support with a precise question."),
("Create an Exam-Day Paper Map","Decide reading time, question order, time caps and the exit rule for a stuck adjustment before entering the hall."),
("Use Examiner Comments as Feedback","Convert recurring examiner observations into a presentation and mistake checklist for future answers."),
("Stop Passive Revision","Closed-book recall and fresh problem solving must dominate the final rounds; rereading alone creates familiarity, not retrieval.")
],
"Teaching System": [
("K1 Kahaani: Learn the Why Before the Rule","A memorable business situation gives the accounting rule a human cause, consequence and retrieval cue."),
("K2 Koncept: Read the Official Principle","Definitions, recognition criteria, conditions and exceptions should remain anchored to official ICAI material."),
("K3 Karma: Convert Listening into Marks","Practice, correction and repetition are the stage where understood concepts become independently usable."),
("Connect Every Rule Back to the Story","When the formal wording feels abstract, recall the decision in the story that the rule was designed to improve."),
("Use Real-World References Carefully","Professional examples help students see timing, measurement and classification choices beyond a textbook illustration."),
("Practise Exact Exam Presentation","Working notes, headings and Schedule III structures need to become automatic through repeated written use."),
("Record the Possible Mistake Beside the Question","A solution becomes more valuable when it includes the trap that could cause the same error again."),
("Identify the Examiner’s Trigger","Ask which condition, exception or adjustment the paper-setter is testing before beginning calculations."),
("Use Three Physical or Digital Books","Separate theory and revision, question practice, and strategy so each resource has a clear job."),
("Run Daily, Chapter and Cumulative Assessment","Frequent low-stakes practice feeds chapter tests, and chapter learning feeds full-syllabus rehearsal."),
("Use Difficulty Levels Deliberately","Move from foundation to standard to advanced questions after the earlier level can be solved without support."),
("Track Accuracy by Topic","A single overall score can hide weaknesses; topic-level accuracy points to the exact repair area."),
("Reserve Time for Mental Readiness","Preparation reviews should include confidence, fear, workload and recovery—not only chapter completion."),
("Use Anonymous Doubt Channels","Students often ask better questions when embarrassment is removed from the process."),
("Release Revision After Chapter Completion","A condensed chapter revision works best after full learning and practice, not as a substitute for them."),
("End Every Session with Independent Application","The student should finish by doing something without the teacher: recall, classify, calculate or explain.")
],
"AS 2 & Accounting Standards": [
("Why Inventory Is Lower of Cost and NRV","The rule prevents recognition of unrealised profit while recognising a decline when inventory cannot recover its carrying amount."),
("Define Inventory Through Economic Use","Inventory includes items held for sale, in production for sale, or consumed in producing goods or services for sale."),
("Test Whether AS 2 Applies","Check the nature of the item and specific scope exclusions before applying measurement rules."),
("Use Risk and Reward for Goods in Transit","Inventory belongs to the entity that bears the relevant economic risks and rewards, not automatically the party holding the invoice."),
("Build Cost from Three Components","Combine purchase, conversion and eligible other costs incurred to bring inventory to its present location and condition."),
("Exclude Recoverable Taxes from Purchase Cost","A tax recoverable from the authority does not form inventory cost, while non-recoverable duties may do so."),
("Absorb Fixed Overheads at Normal Capacity","Using normal capacity avoids inflating inventory cost when production is abnormally low."),
("Treat Abnormal Waste as Period Expense","Unexpected waste does not improve inventory’s location or condition and should not be loaded onto good units."),
("Distinguish Necessary and Ordinary Storage","Storage is included only when it is a necessary stage before a further production process."),
("Allocate Joint Cost Rationally","Common costs up to split-off are allocated on a rational, consistent basis; by-product NRV commonly reduces main-product cost."),
("Choose FIFO or Weighted Average Consistently","Interchangeable inventory uses an accepted cost formula applied consistently to items of similar nature and use."),
("Use Specific Identification for Unique Items","Actual item cost is appropriate when inventory is individually identifiable and not ordinarily interchangeable."),
("Understand Margin Versus Mark-Up","Margin is measured on selling price while mark-up is measured on cost; confusing the base changes the answer."),
("Compute NRV in Three Steps","Start with estimated selling price, then deduct completion cost and costs necessary to make the sale."),
("Compare Cost and NRV Item by Item","A profitable item should not normally offset a loss on another item; related grouping is an exception, not the default."),
("Assess Raw Materials Through Finished Goods","Raw materials generally stay at cost when finished goods are expected to recover total cost; otherwise replacement cost becomes relevant."),
("Reassess and Reverse a Write-Down","If the cause of a prior reduction no longer exists, reversal is limited so carrying amount never exceeds original cost."),
("Disclose Policy, Formula and Classification","Financial statements explain the measurement policy, cost formula and carrying amounts by appropriate inventory class."),
("Read a Standard in Five Boxes","Organise every standard into scope, recognition, measurement, presentation and disclosure."),
("Write Rule, Reason and Application","A three-column note connects official wording to its purpose and a short examination example.")
],
"Revision & Exam Execution": [
("Round 1: Rebuild Understanding","Reconnect each principle with representative questions and create the first reliable error register."),
("Round 2: Compress and Mix","Use shorter notes and mixed questions so chapter labels no longer provide the answer trigger."),
("Round 3: Deliver Under Time","Practise closed-book recall, working-note structures and full-paper execution without opening new sources."),
("Use Spaced Retrieval Dates","Schedule a concept to return after increasing intervals rather than revising only when it feels forgotten."),
("Perform a Five-Minute Brain Dump","Write everything remembered before opening notes; the gaps show what revision should target."),
("Create a One-Page Chapter Map","Place scope, core rule, calculation path, exceptions and common errors on one connected page."),
("Use Red-Amber-Green Status Honestly","Green means independent exam-level performance, not lecture completion; amber and red determine next-week allocation."),
("Build an Error-to-Action Register","Every recorded mistake must end with a specific replacement behaviour for the next attempt."),
("Reattempt Without Seeing the Solution","A corrected answer copied from a solution does not prove the error has been repaired."),
("Use Time Caps by Mark Weight","Allocate minutes in proportion to marks and leave a question when the cap threatens the remainder of the paper."),
("Train Question Selection","Read the paper, identify high-confidence starts and avoid allowing the first difficult question to control the exam."),
("Protect Working-Note Legibility","Use labels, units and cross-references so method remains visible to the examiner."),
("Run a Post-Mock Audit","Compare attempted marks, earned marks, time used, error types and unattempted opportunities."),
("Create a Final 48-Hour Source List","Limit the final revision to predetermined summary notes, formulas, formats and the personal error register."),
("Use Gap Days by Subject Demand","Allocate writing, recall or MCQ practice according to the next paper instead of repeating one generic routine."),
("Recover After a Difficult Paper","Close the completed subject, avoid answer comparison and begin the next paper’s planned first block.")
]
}

action_map = {
"Daily Discipline":["Apply the behaviour for the next seven days.","Record completion in the nightly Bucket 0 tick.","Review what made the habit easy or difficult on Sunday."],
"Foundation Strategy":["Write the output required for this task.","Attempt it under the correct paper conditions.","Put every repeatable mistake into the Error Register."],
"CA Inter Strategy":["Connect the task to the relevant syllabus chapter.","Complete one independent exam-level application.","Schedule the next closed-book retrieval."],
"Teaching System":["Start with the Kahaani or purpose.","Read the official Koncept and conditions.","Complete Karma through independent practice."],
"AS 2 & Accounting Standards":["State the applicable rule before calculating.","Show the decision path in working notes.","Check scope, exceptions and disclosure points."],
"Revision & Exam Execution":["Recall before reopening notes.","Practise under a defined time cap.","Audit the attempt and repair the error."]
}

def friendly(title):
    x = re.sub(r"\.pdf$","",title,flags=re.I)
    x = re.sub(r"^(?:\\d+_)?M\\d+_C\\d+_U\\d+_\\s*","",x)
    x = re.sub(r"^(?:P\\d+\\s+NB\\s+\\d+\\s*-?\\s*)","",x,flags=re.I)
    x = x.replace("_"," ").replace("  "," ").strip(" -")
    return x

def resource_summary(note):
    name=friendly(note["title"]); cat=note["category"]
    if "Question Bank" in cat:
        return f"Use {name} as an examination-practice resource: attempt first, compare with the supplied answer where applicable, and convert every repeatable gap into an Error Register action."
    if "Bare Accounting" in cat:
        return f"Use {name} to verify the official wording, scope, principles and disclosures. Read it beside concise notes so memory remains anchored to the authoritative text."
    if "Revision" in cat or "Newton" in cat:
        return f"Use {name} for compressed recall after complete learning. Test retrieval before reading and return to Layer 1 whenever a rule or adjustment is unclear."
    if "Annotated" in cat:
        return f"Use {name} as a guided Layer 1 learning resource. Follow the annotations, connect them to official material and complete the related questions independently."
    if "Study Material" in cat:
        return f"Use {name} as the primary official learning source. Mark definitions, conditions, illustrations and presentation requirements before creating shorter revision layers."
    if "Practical" in cat:
        return f"Use {name} to observe how accounting information is presented in an actual corporate context. Trace the relevant policy, note and financial-statement impact."
    return f"Use {name} for its stated Advanced Accounting learning purpose, then connect it to a chapter summary, question practice and scheduled revision."

items=[]; counter=1
for cat, rows in themes.items():
    for title, summary in rows:
        items.append({"id":f"K{counter:03}","title":title,"category":cat,"sourceType":"Written Guide","summary":summary,
          "subject":"CA Foundation" if cat=="Foundation Strategy" else "Advanced Accounting" if cat in ("AS 2 & Accounting Standards","Teaching System") else "CA Student Strategy",
          "chapter":"AS 2 — Inventories" if "AS 2" in title or "Inventory" in title else "General","attempt":"All attempts","revisionLayer":"Guidance","access":"Free","freshness":"Updated","difficulty":"Foundation" if cat=="Foundation Strategy" else "Standard","updated":"28 July 2026","recommendation":"Recommended when this matches your present study problem.",
          "actions":action_map[cat],"mistakes":["Reading without producing a recall output.","Moving on before the idea is independently usable."],
          "sourceUrl":{"Daily Discipline":"viewer.html?experience=bucket-0","Foundation Strategy":"viewer.html?experience=ca-foundation-sep26","CA Inter Strategy":"viewer.html?experience=ca-inter-sep26","Teaching System":"viewer.html?experience=teaching-style","AS 2 & Accounting Standards":"viewer.html?experience=koncept","Revision & Exam Execution":"student-learning.html#revision"}[cat],
          "sourceLabel":"Open the connected CAPRANAV source","tags":[cat,"CA Student","Action Guide"]}); counter+=1
for note in notes:
    name=friendly(note["title"])
    as_match=re.search(r"\\bAS\\s*0?(\\d+)\\b",name,re.I)
    attempt_match=re.search(r"\\b(Jan|May|Sep|Nov)(20\\d{2})\\b",name,re.I)
    chapter=(f"AS {int(as_match.group(1))}" if as_match else "Advanced Accounting — General")
    attempt=(attempt_match.group(1).title()+" "+attempt_match.group(2) if attempt_match else "All attempts")
    difficulty=("Exam Practice" if note["category"]=="Question Bank" else "Revision" if "Revision" in note["category"] or "Newton" in note["category"] else "Foundation")
    recommendation=("Attempt before opening the answer and record recurring errors." if note["category"]=="Question Bank" else "Use after complete learning for focused recall." if difficulty=="Revision" else "Use as the primary source for concept learning.")
    items.append({"id":f"K{counter:03}","title":friendly(note["title"]),"category":"Resource Guides","sourceType":note["category"],"summary":resource_summary(note),
      "subject":"Advanced Accounting","chapter":chapter,"attempt":attempt,"revisionLayer":note["layer"],"access":"Free","freshness":"Updated","difficulty":difficulty,"updated":"27 July 2026","recommendation":recommendation,
      "actions":["Open the source and identify its exact chapter or task.","Create a measurable reading, attempt or revision output.","Link errors or weak areas to the next practice session."],
      "mistakes":["Downloading the file without scheduling its use.","Using a revision source as a substitute for complete concept learning."],
      "sourceUrl":note["preview"],"downloadUrl":note["download"],"sourceLabel":"Open source resource","tags":[note["layer"],note["category"],"Advanced Accounting"]}); counter+=1

out = "window.CAPRANAV_KNOWLEDGE = " + json.dumps({"updated":"28 July 2026","count":len(items),"items":items},ensure_ascii=False,separators=(",",":")) + ";\n"
(ROOT/"assets"/"knowledge-data.js").write_text(out,encoding="utf-8")
print(f"Built {len(items)} knowledge entries")
