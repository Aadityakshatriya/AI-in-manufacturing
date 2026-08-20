import fs from "node:fs/promises";

const artifactToolModule = process.env.ARTIFACT_TOOL_MODULE;
if (!artifactToolModule) {
  throw new Error("Set ARTIFACT_TOOL_MODULE to the artifact-tool module file URL.");
}
const { SpreadsheetFile, Workbook } = await import(artifactToolModule);

const specs = [
  {
    csv: "research/opportunity-universe-1000.csv",
    xlsx: "research/opportunity-universe-1000.xlsx",
    sheetName: "1,000 Opportunities",
    header: "A1:J1",
    body: "A2:J1001",
    widths: [15, 22, 34, 28, 62, 46, 50, 48, 38, 25],
  },
  {
    csv: "research/project-longlist-100.csv",
    xlsx: "research/project-longlist-100.xlsx",
    sheetName: "100 Projects",
    header: "A1:H1",
    body: "A2:H101",
    widths: [13, 22, 48, 72, 48, 52, 40, 58],
  },
];

for (const spec of specs) {
  const csvText = await fs.readFile(spec.csv, "utf8");
  const workbook = await Workbook.fromCSV(csvText, { sheetName: spec.sheetName });
  const sheet = workbook.worksheets.getItem(spec.sheetName);

  sheet.getRange(spec.header).format = {
    fill: "#17324D",
    font: { bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
    wrapText: true,
  };
  sheet.getRange(spec.body).format = {
    verticalAlignment: "top",
    wrapText: true,
  };
  sheet.freezePanes.freezeRows(1);

  for (let i = 0; i < spec.widths.length; i += 1) {
    const column = String.fromCharCode("A".charCodeAt(0) + i);
    sheet.getRange(`${column}:${column}`).format.columnWidth = spec.widths[i];
  }

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(spec.xlsx);

  if (spec.sheetName === "100 Projects") {
    const preview = await workbook.render({
      sheetName: spec.sheetName,
      range: "A1:H15",
      scale: 0.7,
      format: "png",
    });
    await fs.writeFile(
      "research/project-longlist-preview.png",
      new Uint8Array(await preview.arrayBuffer()),
    );
  }
}

console.log("Created and rendered the catalog workbooks.");
