#!/usr/bin/env node
/**
 * report_script.js
 * Reads a JSON payload and produces a DOCX report.
 * Usage: node report_script.js payload.json output.docx
 */

"use strict";

const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, LevelFormat,
  BorderStyle, WidthType, ShadingType, VerticalAlign,
  PageNumberElement, PageBreak, TabStopType, TabStopPosition,
} = require("docx");

// ─── Load payload ────────────────────────────────────────────────
const [,, payloadPath, outputPath] = process.argv;
const data = JSON.parse(fs.readFileSync(payloadPath, "utf8"));
const { meta, summary, scores, key_risks, findings,
        sections_with_findings, action_buckets, horizon_order,
        horizon_labels, suppressed_findings, unknown_log, response_log } = data;

// ─── Colour palette ──────────────────────────────────────────────
const C = {
  urgent:   "C0392B",
  concern:  "E67E22",
  watch:    "F1C40F",
  healthy:  "27AE60",
  accent:   "1A5276",   // deep navy for headings
  mid:      "2E86C1",   // medium blue
  light:    "D6EAF8",   // light blue fill
  silver:   "BDC3C7",
  offwhite: "F8F9FA",
  white:    "FFFFFF",
  black:    "000000",
  text:     "2C3E50",
  faint:    "7F8C8D",
};

const SEV_COLORS = { urgent: C.urgent, concern: C.concern, watch: C.watch, healthy: C.healthy };

// ─── Page geometry ───────────────────────────────────────────────
const PAGE_W   = 12240;  // US Letter, DXA
const PAGE_H   = 15840;
const MARGIN   = 1080;   // 0.75 inch
const CONTENT  = PAGE_W - MARGIN * 2;  // 10080 DXA

// ─── Typography helpers ──────────────────────────────────────────
function run(text, opts = {}) {
  return new TextRun({ text: String(text || ""), font: "Arial", size: opts.size || 22,
    bold: opts.bold, italic: opts.italic, color: opts.color || C.text,
    break: opts.break });
}

function para(children, opts = {}) {
  const ch = Array.isArray(children) ? children : [run(children, opts)];
  return new Paragraph({
    children: ch,
    alignment: opts.align || AlignmentType.LEFT,
    spacing: { before: opts.before ?? 80, after: opts.after ?? 80,
               line: opts.line ?? 276, lineRule: "auto" },
    indent: opts.indent ? { left: opts.indent } : undefined,
    heading: opts.heading,
    numbering: opts.numbering,
    border: opts.border,
    shading: opts.shading,
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, font: "Arial", size: 36, bold: true, color: C.accent })],
    spacing: { before: 320, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.mid, space: 1 } },
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, font: "Arial", size: 28, bold: true, color: C.accent })],
    spacing: { before: 240, after: 100 },
  });
}

function h3(text, color) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    children: [new TextRun({ text, font: "Arial", size: 24, bold: true, color: color || C.text })],
    spacing: { before: 180, after: 80 },
  });
}

function spacer(pts = 120) {
  return para([run("")], { before: 0, after: pts });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function labelValue(label, value) {
  if (!value) return null;
  return para([
    run(label + ": ", { bold: true, size: 20, color: C.faint }),
    run(value,        { size: 20 }),
  ], { before: 40, after: 40 });
}

// ─── Severity badge (inline coloured text) ───────────────────────
function sevRun(severity) {
  const label = { urgent: "URGENT", concern: "CONCERN", watch: "WATCH", healthy: "HEALTHY" };
  return new TextRun({
    text: " " + (label[severity] || severity.toUpperCase()) + " ",
    font: "Arial", size: 18, bold: true,
    color: SEV_COLORS[severity] || C.text,
  });
}

// ─── Shaded box (single-cell table trick) ───────────────────────
function shadedBox(children, fillColor, opts) {
  const border = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const cellChildren = Array.isArray(children) ? children : [children];
  const tc = new TableCell({
    borders: { top: border, bottom: border, left: border, right: border },
    shading: { fill: fillColor || C.offwhite, type: ShadingType.CLEAR },
    margins: { top: 120, bottom: 120, left: 180, right: 180 },
    children: cellChildren,
    width: { size: CONTENT, type: WidthType.DXA },
    verticalAlign: VerticalAlign.TOP,
  });
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: [CONTENT],
    rows: [new TableRow({ children: [tc] })],
  });
}

// ─── Cell helper ────────────────────────────────────────────────
function cell(children, widthDxa, opts = {}) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "DDDDDD" };
  return new TableCell({
    children: Array.isArray(children) ? children : [children],
    width: { size: widthDxa, type: WidthType.DXA },
    borders: { top: border, bottom: border, left: border, right: border },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.TOP,
  });
}

// ─── SECTION 1: Cover Page ───────────────────────────────────────
function buildCover() {
  const items = [];

  // Big school name
  items.push(spacer(1440));
  items.push(new Paragraph({
    children: [new TextRun({ text: meta.school_name || "School Name", font: "Arial",
      size: 64, bold: true, color: C.accent })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 160 },
  }));

  // Mission statement
  if (meta.school_mission) {
    items.push(new Paragraph({
      children: [new TextRun({ text: meta.school_mission, font: "Arial",
        size: 24, italic: true, color: C.faint })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 480 },
    }));
  } else {
    items.push(spacer(480));
  }

  // Horizontal rule
  items.push(new Paragraph({
    children: [run("")],
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: C.mid, space: 1 } },
    spacing: { before: 0, after: 480 },
  }));

  // Report title
  items.push(new Paragraph({
    children: [new TextRun({ text: "IT State of the System Report",
      font: "Arial", size: 40, bold: true, color: C.text })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 120 },
  }));

  // Prepared for
  if (meta.respondent_name || meta.respondent_role) {
    items.push(new Paragraph({
      children: [new TextRun({ text: "Prepared for", font: "Arial",
        size: 22, color: C.faint })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 60 },
    }));
    if (meta.respondent_name) {
      items.push(new Paragraph({
        children: [new TextRun({ text: meta.respondent_name,
          font: "Arial", size: 26, bold: true, color: C.text })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 40 },
      }));
    }
    if (meta.respondent_role) {
      items.push(new Paragraph({
        children: [new TextRun({ text: meta.respondent_role,
          font: "Arial", size: 22, color: C.faint })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 40 },
      }));
    }
  }

  items.push(spacer(240));
  items.push(new Paragraph({
    children: [new TextRun({ text: meta.report_date,
      font: "Arial", size: 20, color: C.faint })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 0 },
  }));

  return items;
}

// ─── SECTION 2: Executive Summary ───────────────────────────────
function buildExecutiveSummary() {
  const items = [pageBreak(), h1("Executive Summary")];

  // Score table
  if (scores && scores.length > 0) {
    items.push(h2("Section Scores"));
    const hdrFill = C.accent;
    const hdrRun = (t) => new TextRun({ text: t, font: "Arial", size: 20, bold: true, color: C.white });
    const colW = [3600, 2400, 1680, 2400];

    const hdrRow = new TableRow({ children: [
      cell([para([hdrRun("Section")],         { before: 0, after: 0 })], colW[0], { fill: hdrFill }),
      cell([para([hdrRun("Score")],           { before: 0, after: 0, align: AlignmentType.CENTER })], colW[1], { fill: hdrFill }),
      cell([para([hdrRun("Status")],          { before: 0, after: 0, align: AlignmentType.CENTER })], colW[2], { fill: hdrFill }),
      cell([para([hdrRun("Answered")],        { before: 0, after: 0, align: AlignmentType.CENTER })], colW[3], { fill: hdrFill }),
    ]});

    const dataRows = scores.map((s, i) => {
      const isCtx = s.max_pts === 0;
      const scoreText = isCtx ? "Context only" : `${s.earned} / ${s.max_pts} (${s.pct}%)`;
      const sevColor = SEV_COLORS[s.severity] || C.text;
      const rowFill = i % 2 === 0 ? C.white : C.offwhite;
      return new TableRow({ children: [
        cell([para([run(`${s.section_id}. ${s.title}`, { size: 20 })], { before: 0, after: 0 })],
             colW[0], { fill: rowFill }),
        cell([para([run(scoreText, { size: 20 })], { before: 0, after: 0, align: AlignmentType.CENTER })],
             colW[1], { fill: rowFill }),
        cell([para([new TextRun({ text: isCtx ? "—" : s.severity.toUpperCase(),
               font: "Arial", size: 18, bold: true, color: isCtx ? C.faint : sevColor })],
               { before: 0, after: 0, align: AlignmentType.CENTER })],
             colW[2], { fill: rowFill }),
        cell([para([run(`${s.answered} answered`, { size: 18 })],
               { before: 0, after: 0, align: AlignmentType.CENTER })],
             colW[3], { fill: rowFill }),
      ]});
    });

    items.push(new Table({
      width: { size: CONTENT, type: WidthType.DXA },
      columnWidths: colW,
      rows: [hdrRow, ...dataRows],
    }));
    items.push(spacer(200));
  }

  // Finding counts
  items.push(h2("Assessment Overview"));
  items.push(para([
    run(`This assessment identified `),
    run(`${summary.urgent_count} urgent`, { bold: true, color: C.urgent }),
    run(`, `),
    run(`${summary.concern_count} concern`, { bold: true, color: C.concern }),
    run(`, and `),
    run(`${summary.watch_count} watch`, { bold: true, color: C.watch }),
    run(` level findings across ${data.sections_with_findings.length} sections. ` +
        `${summary.suppressed_count} additional findings were absorbed into composite findings and are ` +
        `listed in the appendix for traceability.`),
  ], { before: 80, after: 120, size: 22 }));

  // Mandatory urgent findings in Executive Summary
  const mandatoryInExecSummary = new Set([
    "F2-C01","F7-C01","F3-017","F3-C01","F3-C02",
    "F5-C02","F6-C01","F6-C02","F8-C01","F8-008","F9-C01",
  ]);
  const execFindings = findings.filter(f =>
    mandatoryInExecSummary.has(f.finding_id) || f.severity === "urgent"
  );

  if (execFindings.length > 0) {
    items.push(h2("Priority Findings"));
    items.push(para(
      "The following findings require immediate attention or leadership awareness. " +
      "They appear here in addition to the full findings section.",
      { before: 60, after: 120, size: 22 }
    ));

    for (const f of execFindings) {
      const boxColor = f.severity === "urgent" ? "FDEDEC" : "FEF9E7";
      const boxBorder = SEV_COLORS[f.severity] || C.text;
      items.push(shadedBox([
        new Paragraph({
          children: [
            sevRun(f.severity),
            run("  " + f.title, { bold: true, size: 22 }),
          ],
          spacing: { before: 0, after: 60 },
        }),
        para(f.description, { before: 0, after: 0, size: 20 }),
        ...(f.notes_passthrough ? [
          para([run("IT person noted: ", { italic: true, bold: true, size: 18, color: C.faint }),
                run(f.notes_passthrough, { italic: true, size: 18, color: C.faint })],
               { before: 60, after: 0 }),
        ] : []),
      ], boxColor));
      items.push(spacer(80));
    }
  }

  return items;
}

// ─── SECTION 3: Key Risks ────────────────────────────────────────
function buildKeyRisks() {
  if (!key_risks || key_risks.length === 0) return [];
  const items = [pageBreak(), h1("Key Risks")];

  items.push(para(
    "The following named risk groups aggregate related findings from across the assessment. " +
    "Addressing the primary finding in each group has the broadest impact on the school's " +
    "overall IT resilience.",
    { before: 80, after: 160, size: 22 }
  ));

  for (const group of key_risks) {
    const sevColor = SEV_COLORS[group.severity] || C.text;
    const boxFill  = group.severity === "urgent" ? "FDEDEC"
                   : group.severity === "concern" ? "FEF9E7"
                   : "FDFEFE";

    // Find contributing findings
    const contrib = findings.filter(f => group.finding_ids.includes(f.finding_id));

    items.push(shadedBox([
      new Paragraph({
        children: [
          sevRun(group.severity),
          run("  " + group.title, { bold: true, size: 24 }),
        ],
        spacing: { before: 0, after: 80 },
      }),
      ...contrib.map(f =>
        para([
          run(`${f.finding_id}  `, { bold: true, size: 19, color: C.faint }),
          run(f.title, { size: 19 }),
        ], { before: 40, after: 20, indent: 120,
             numbering: undefined })
      ),
    ], boxFill));
    items.push(spacer(100));
  }

  return items;
}

// ─── SECTION 4: Section-by-Section Findings ─────────────────────
function buildSectionFindings() {
  const items = [pageBreak(), h1("Section-by-Section Findings")];

  items.push(para(
    "This section presents all findings by area. Within each area, findings are ordered " +
    "by severity (urgent first) then by finding ID. Actions are listed under each finding " +
    "they belong to.",
    { before: 80, after: 160, size: 22 }
  ));

  for (const sec of sections_with_findings) {
    items.push(h2(`Section ${sec.section_id}: ${sec.section_name}`));

    for (const f of sec.findings) {
      const sevColor = SEV_COLORS[f.severity] || C.text;
      const boxFill  = f.severity === "urgent" ? "FDEDEC"
                     : f.severity === "concern" ? "FEF9E7"
                     : "FDFEFE";

      // Finding header
      items.push(new Paragraph({
        children: [
          sevRun(f.severity),
          run("  " + f.title, { bold: true, size: 22 }),
          run("  ", { size: 18 }),
          run(f.finding_id, { size: 16, color: C.faint }),
        ],
        spacing: { before: 160, after: 80 },
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: sevColor, space: 6 } },
        indent: { left: 180 },
      }));

      // Description
      items.push(para(f.description, { before: 0, after: 80, size: 21, indent: 180 }));

      // Notes passthrough
      if (f.notes_passthrough) {
        items.push(shadedBox([
          para([
            run("IT person noted: ", { bold: true, size: 19, italic: true, color: C.faint }),
            run(f.notes_passthrough, { size: 19, italic: true }),
          ], { before: 0, after: 0 }),
        ], C.light));
        items.push(spacer(60));
      }

      // Plain language note
      if (f.plain_language_note) {
        items.push(shadedBox([
          para([
            run("Note: ", { bold: true, size: 18, color: C.mid }),
            run(f.plain_language_note, { size: 18, color: C.text }),
          ], { before: 0, after: 0 }),
        ], "EBF5FB"));
        items.push(spacer(60));
      }

      // Amplification flag
      if (f.amplification_flag) {
        items.push(para([
          run("📎 ", { size: 18 }),
          run("This finding is harder to resolve while documentation is absent — addressing Section 9 findings first will make this easier to close systematically.",
            { size: 18, italic: true, color: C.faint }),
        ], { before: 0, after: 80, indent: 180 }));
      }

      // Actions
      if (f.actions && f.actions.length > 0) {
        items.push(para("Recommended actions:", { before: 80, after: 40, size: 20,
          bold: true, indent: 180 }));
        for (const act of f.actions) {
          const horizonText = act.constraint_flag
            ? `${act.horizon_label}  ⚠ Budget constraint noted`
            : act.horizon_label;
          items.push(new Paragraph({
            numbering: { reference: "action-bullets", level: 0 },
            children: [
              run(act.description, { size: 20 }),
              run(`  [${horizonText}]`, { size: 18, color: C.faint, italic: true }),
              ...(act.schedule_label ? [run(`  — ${act.schedule_label}`, { size: 17, color: C.faint, italic: true })] : []),
            ],
            spacing: { before: 40, after: 40 },
          }));
        }
      }
    }

    items.push(spacer(120));
  }

  return items;
}

// ─── SECTION 5: Action Plan ──────────────────────────────────────
function buildActionPlan() {
  const items = [pageBreak(), h1("Action Plan")];

  items.push(para(
    "Actions are organised by time horizon. Within each horizon, items are grouped by " +
    "section. Items marked with ⚠ are subject to budget or staffing constraints noted " +
    "during the assessment.",
    { before: 80, after: 160, size: 22 }
  ));

  const SEV_ORDER = { urgent: 0, concern: 1, watch: 2 };

  for (const horizon of horizon_order) {
    const bucket = action_buckets[horizon];
    if (!bucket || bucket.length === 0) continue;

    items.push(h2(horizon_labels[horizon]));

    // Group by section within the horizon
    const bySection = {};
    for (const act of bucket) {
      const sid = act.section_id;
      if (!bySection[sid]) bySection[sid] = { name: act.section_name, actions: [] };
      bySection[sid].actions.push(act);
    }

    for (const [sid, group] of Object.entries(bySection).sort((a,b) => a[0].localeCompare(b[0]))) {
      items.push(h3(`Section ${sid}: ${group.name}`));
      // Sort by severity within section
      group.actions.sort((a,b) => (SEV_ORDER[a.severity]??9) - (SEV_ORDER[b.severity]??9));

      for (const act of group.actions) {
        const prefix = act.constraint_flag ? "⚠ " : "";
        const label  = act.schedule_label ? `  — ${act.schedule_label}` : "";
        items.push(new Paragraph({
          numbering: { reference: "action-bullets", level: 0 },
          children: [
            ...(act.user_confirmed ? [run("⭐ ", { size: 20 })] : []),
            run(`[${act.finding_id}] `, { size: 18, color: C.faint }),
            run(prefix + act.description, { size: 20 }),
            run(label, { size: 18, italic: true, color: C.faint }),
          ],
          spacing: { before: 40, after: 60 },
        }));
      }
      items.push(spacer(80));
    }
  }

  return items;
}

// ─── SECTION 6: Appendix ────────────────────────────────────────
function buildAppendix() {
  const items = [pageBreak(), h1("Appendix")];

  // A. Suppressed findings
  if (suppressed_findings && suppressed_findings.length > 0) {
    items.push(h2("A. Composite Finding Traceability"));
    items.push(para(
      "The following findings were absorbed into composite findings and are not shown " +
      "in the main findings section. Their recommended actions are included in the " +
      "composite finding that supersedes them.",
      { before: 60, after: 120, size: 20 }
    ));
    for (const f of suppressed_findings) {
      items.push(para([
        run(`${f.finding_id}`, { bold: true, size: 20, color: C.faint }),
        run(`  ${f.title}`, { size: 20 }),
        run(`  → absorbed by ${f.suppressed_by}`, { size: 18, italic: true, color: C.faint }),
      ], { before: 40, after: 40 }));
    }
    items.push(spacer(160));
  }

  // B. Unknown answers log
  if (unknown_log && unknown_log.length > 0) {
    items.push(h2("B. Unknown Answer Log"));
    items.push(para(
      `${unknown_log.length} question${unknown_log.length !== 1 ? "s were" : " was"} answered as "I don't know." ` +
      "Unknown answers are included in the section denominator and score zero points. " +
      "Each represents a gap in knowledge that should be investigated.",
      { before: 60, after: 120, size: 20 }
    ));

    // Group by section
    const bySec = {};
    for (const u of unknown_log) {
      if (!bySec[u.section_id]) bySec[u.section_id] = [];
      bySec[u.section_id].push(u.question_id);
    }
    for (const [sid, qids] of Object.entries(bySec).sort()) {
      items.push(para(`Section ${sid}: ${qids.join(", ")}`,
        { before: 40, after: 40, size: 20, indent: 360 }));
    }
    items.push(spacer(160));
  }

  // C. Full response log
  items.push(h2("C. Full Response Log"));
  items.push(para(
    "Complete record of all answers submitted during this assessment.",
    { before: 60, after: 120, size: 20 }
  ));

  const colW2 = [1080, 8280];
  const logRows = response_log.map((r, i) => {
    const rowFill = i % 2 === 0 ? C.white : C.offwhite;
    const statusColor = r.status === "unknown" ? C.concern
                      : r.status === "skipped"  ? C.silver : C.text;
    return new TableRow({ children: [
      cell([para([run(r.question_id, { size: 17, color: C.faint })], { before: 0, after: 0 })],
           colW2[0], { fill: rowFill }),
      cell([para([
        run(r.status === "unanswered" ? "(not answered)" : r.answer || r.status,
          { size: 17, color: statusColor }),
      ], { before: 0, after: 0 })], colW2[1], { fill: rowFill }),
    ]});
  });

  if (logRows.length > 0) {
    items.push(new Table({
      width: { size: CONTENT, type: WidthType.DXA },
      columnWidths: colW2,
      rows: logRows,
    }));
  }

  return items;
}

// ─── HEADER / FOOTER ────────────────────────────────────────────
function makeHeader() {
  return new Header({
    children: [new Paragraph({
      children: [
        new TextRun({ text: meta.school_name || "", font: "Arial", size: 18, color: C.faint }),
        new TextRun({ text: "\t", font: "Arial", size: 18 }),
        new TextRun({ text: "IT State of the System Report", font: "Arial", size: 18, color: C.faint }),
      ],
      tabStops: [{ type: TabStopType.RIGHT, position: CONTENT }],
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.silver, space: 1 } },
      spacing: { before: 0, after: 80 },
    })],
  });
}

function makeFooter(confidenceCaveat) {
  const children = [];

  if (confidenceCaveat) {
    children.push(new Paragraph({
      children: [new TextRun({ text: "⚠ " + confidenceCaveat, font: "Arial",
        size: 16, italic: true, color: C.concern })],
      spacing: { before: 0, after: 40 },
      border: { top: { style: BorderStyle.SINGLE, size: 2, color: C.silver, space: 1 } },
    }));
  }

  children.push(new Paragraph({
    children: [
      new TextRun({ text: meta.report_date, font: "Arial", size: 17, color: C.faint }),
      new TextRun({ text: "\t", font: "Arial", size: 17 }),
      new TextRun({ text: "Page ", font: "Arial", size: 17, color: C.faint }),
      new PageNumberElement(),
    ],
    tabStops: [{ type: TabStopType.RIGHT, position: CONTENT }],
    border: confidenceCaveat ? undefined : {
      top: { style: BorderStyle.SINGLE, size: 2, color: C.silver, space: 1 }
    },
    spacing: { before: 40, after: 0 },
  }));

  return new Footer({ children });
}

// ─── ASSEMBLE DOCUMENT ───────────────────────────────────────────
function buildDocument() {
  const header  = makeHeader();
  const footer  = makeFooter(meta.confidence_caveat);

  const allChildren = [
    ...buildCover(),
    ...buildExecutiveSummary(),
    ...buildKeyRisks(),
    ...buildSectionFindings(),
    ...buildActionPlan(),
    ...buildAppendix(),
  ];

  return new Document({
    styles: {
      default: {
        document: { run: { font: "Arial", size: 22, color: C.text } },
      },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 36, bold: true, font: "Arial", color: C.accent },
          paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 28, bold: true, font: "Arial", color: C.accent },
          paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 1 } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 24, bold: true, font: "Arial", color: C.text },
          paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
      ],
    },
    numbering: {
      config: [
        { reference: "action-bullets",
          levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 540, hanging: 260 } } } }] },
      ],
    },
    sections: [{
      properties: {
        page: {
          size: { width: PAGE_W, height: PAGE_H },
          margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
        },
      },
      headers: { default: header },
      footers: { default: footer },
      children: allChildren,
    }],
  });
}

// ─── MAIN ────────────────────────────────────────────────────────
(async () => {
  try {
    const doc    = buildDocument();
    const buffer = await Packer.toBuffer(doc);
    fs.writeFileSync(outputPath, buffer);
    process.exit(0);
  } catch (err) {
    console.error("Report generation error:", err.message);
    console.error(err.stack);
    process.exit(1);
  }
})();
