import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "first_run/output/20260921-ca-practice/ca_inter_practice_index_v2.xlsx";
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const summary = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 10000,
  tableMaxRows: 8,
  tableMaxCols: 30,
  tableMaxCellChars: 120,
});
console.log(summary.ndjson);
for (const sheetName of ["Summary", "Questions", "Study topics"]) {
  const view = await workbook.inspect({
    kind: "region",
    sheetId: sheetName,
    range: sheetName === "Summary" ? "A1:Z45" : "A1:AF8",
    maxChars: 15000,
  });
  console.log(`\n--- ${sheetName} ---\n${view.ndjson}`);
}
for (const sheetName of ["Summary", "Questions", "Study topics"]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.mkdir(".tmp_artifact/previews", { recursive: true });
  await fs.writeFile(`.tmp_artifact/previews/${sheetName.replace(/ /g,"_")}.png`, new Uint8Array(await preview.arrayBuffer()));
}
