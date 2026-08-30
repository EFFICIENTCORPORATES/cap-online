(() => {
  const demos=window.CAPRANAV_AS_DEMOS||[];
  const officialSource="https://www.icai.org/post/bos-int-p1-may2026-exam";
  const examActions={
    "AS 2":"Prepare an include–exclude cost table, then compare cost with net realisable value item by item.",
    "AS 10":"Build one complete PPE cost sheet and a separate depreciation working from available-for-use date.",
    "AS 22":"Separate permanent and timing differences before calculating deferred tax."
  };
  demos.forEach((demo,index)=>{
    const number=demo.id.replace("AS ","");
    const slug=`as-${number}`;
    const overview=demo.steps.map(step=>step[1]).join(" ");
    window.CAPRANAV_GUIDES[slug]={
      title:`${demo.id}: ${demo.title}`,
      eyebrow:"Accounts · Accounting Standards",
      reading:`${10+(index%4)} min read`,
      animation:true,
      asId:demo.id,
      officialSource,
      intro:`This focused guide explains the decision sequence behind ${demo.id}. Read the written rule first, use the controlled demonstration to see the sequence, and then apply it independently to an examination question.`,
      sections:[
        {title:"Concept map",body:overview,action:`Say the four-part ${demo.id} sequence without looking at the page.`},
        ...demo.steps.map((step,stepIndex)=>({
          title:step[0],
          body:`${step[1]} This is step ${stepIndex+1} in the decision sequence. In a question, state the governing principle before inserting figures or preparing the accounting treatment.`,
          action:stepIndex===demo.steps.length-1?(examActions[demo.id]||`Attempt one complete ${demo.id} question.`):`Write one example that demonstrates “${step[0]}”.`
        })),
        {title:"Exam application",body:`A strong ${demo.id} answer should show classification, the applicable rule, a clear working and the resulting accounting or disclosure treatment. Do not begin with a memorised format before identifying what the facts require. Cross-check amendments and examination applicability with the current ICAI material.`,action:examActions[demo.id]||`Attempt one complete ${demo.id} question and add the error to your register.`},
        {title:"Official-source check",body:"This learning explanation is an original student aid aligned to the current ICAI Intermediate Advanced Accounting study-material structure. It does not replace the notified text, statutory requirements or ICAI announcements.",action:`Open the official ICAI source and mark the paragraphs relevant to your ${demo.id} question.`}
      ]
    };
  });
})();
