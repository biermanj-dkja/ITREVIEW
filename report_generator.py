"""
Report Generator for Module 1 — School IT State of the System Report
Uses python-docx to produce the DOCX entirely in Python.
No Node.js or npm dependency required.
"""
import io
from datetime import date
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

class C:
    urgent  = RGBColor(0xC0,0x39,0x2B); concern = RGBColor(0xE6,0x7E,0x22)
    watch   = RGBColor(0xF3,0x9C,0x12); healthy = RGBColor(0x27,0xAE,0x60)
    accent  = RGBColor(0x1A,0x52,0x76); mid     = RGBColor(0x2E,0x86,0xC1)
    text    = RGBColor(0x2C,0x3E,0x50); faint   = RGBColor(0x7F,0x8C,0x8D)
    white   = RGBColor(0xFF,0xFF,0xFF); silver  = RGBColor(0xBD,0xC3,0xC7)

SEV_COLOR = {"urgent":C.urgent,"concern":C.concern,"watch":C.watch,"healthy":C.healthy}
SEV_LABEL = {"urgent":"URGENT","concern":"CONCERN","watch":"WATCH","healthy":"HEALTHY","context_only":"CONTEXT ONLY"}
HORIZON_LABEL = {"immediate":"Immediate","next_30_days":"Within 30 days",
                 "next_90_days":"Within 90 days","next_12_months":"Within 12 months",
                 "strategic_future":"Strategic / Future"}
HORIZON_ORDER = ["immediate","next_30_days","next_90_days","next_12_months","strategic_future"]
SECTION_NAMES = {
    "2":"Governance, Budget, Staffing, and Ownership",
    "3":"Sites, Buildings, Network, and Internet",
    "4":"Identity, Accounts, and Access",
    "5":"Endpoints, Printing, and Classroom Technology",
    "6":"Core Systems, Servers, Vendors, and Contracts",
    "7":"Data Protection, Backup, and Recovery",
    "8":"Security Operations, Filtering, and Safeguards",
    "9":"Documentation and Operational Readiness",
}
SEV_ORDER = {"urgent":0,"concern":1,"watch":2,"healthy":3,"context_only":4}

def _hex(c): return f"{c[0]:02X}{c[1]:02X}{c[2]:02X}"

def _cell_bg(cell, hex_color):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"),"clear"); shd.set(qn("w:color"),"auto"); shd.set(qn("w:fill"),hex_color)
    tcPr.append(shd)

def _cell_border(cell, color="CCCCCC", sz="4"):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top","bottom","left","right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"),"single"); el.set(qn("w:sz"),sz); el.set(qn("w:color"),color)
        tcBorders.append(el)
    tcPr.append(tcBorders)

def _bottom_border(para, hex_color, sz=6):
    pPr = para._p.get_or_add_pPr(); pBdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom"); bot.set(qn("w:val"),"single")
    bot.set(qn("w:sz"),str(sz)); bot.set(qn("w:space"),"1"); bot.set(qn("w:color"),hex_color)
    pBdr.append(bot); pPr.append(pBdr)

def _left_border(para, hex_color, sz=20):
    pPr = para._p.get_or_add_pPr(); pBdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left"); left.set(qn("w:val"),"single")
    left.set(qn("w:sz"),str(sz)); left.set(qn("w:space"),"6"); left.set(qn("w:color"),hex_color)
    pBdr.append(left); pPr.append(pBdr)

def _page_break(doc):
    p = doc.add_paragraph(); run = p.add_run()
    br = OxmlElement("w:br"); br.set(qn("w:type"),"page"); run._r.append(br)

def _run(para, text, bold=False, italic=False, size=11, color=None):
    r = para.add_run(str(text or ""))
    r.bold=bold; r.italic=italic; r.font.size=Pt(size); r.font.color.rgb=color or C.text
    return r

def _para(doc, text="", bold=False, italic=False, size=11, color=None,
          align=WD_ALIGN_PARAGRAPH.LEFT, sb=4, sa=4):
    p = doc.add_paragraph(); p.alignment=align
    p.paragraph_format.space_before=Pt(sb); p.paragraph_format.space_after=Pt(sa)
    if text: _run(p, text, bold=bold, italic=italic, size=size, color=color)
    return p

def _h(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14 if level==1 else 10 if level==2 else 7)
    p.paragraph_format.space_after  = Pt(5)
    r = p.add_run(text); r.bold=True
    r.font.size = Pt(18 if level==1 else 13 if level==2 else 11)
    r.font.color.rgb = C.accent if level < 3 else C.text
    if level==1: _bottom_border(p, _hex(C.mid), sz=8)
    return p

def _box(doc, fill_hex, builder_fn):
    tbl = doc.add_table(rows=1, cols=1); tbl.style="Table Grid"
    cell = tbl.rows[0].cells[0]; _cell_bg(cell, fill_hex); _cell_border(cell)
    for p in list(cell.paragraphs): p._element.getparent().remove(p._element)
    builder_fn(cell)
    if not cell.paragraphs: cell.add_paragraph()
    doc.add_paragraph().paragraph_format.space_after=Pt(4)

def _cp(cell, text="", bold=False, italic=False, size=10, color=None, sb=2, sa=2):
    p=cell.add_paragraph(); p.paragraph_format.space_before=Pt(sb); p.paragraph_format.space_after=Pt(sa)
    if text: _run(p,text,bold=bold,italic=italic,size=size,color=color)
    return p

def _get(answers, qid):
    d=answers.get(qid)
    if not d: return ""
    r=d.get("raw_answer")
    return ", ".join(str(x) for x in r) if isinstance(r,list) else (str(r) if r else "")

def _set_hf(doc, school, report_date, caveat):
    sec = doc.sections[0]
    hdr = sec.header; hdr.is_linked_to_previous=False
    hp = hdr.paragraphs[0] if hdr.paragraphs else hdr.add_paragraph()
    hp.clear(); hp.alignment=WD_ALIGN_PARAGRAPH.LEFT
    _run(hp, f"{school}  ·  IT State of the System Report", size=8, color=C.faint)
    _bottom_border(hp, _hex(C.silver), sz=4)
    ftr = sec.footer; ftr.is_linked_to_previous=False
    for p in list(ftr.paragraphs): p._element.getparent().remove(p._element)
    if caveat:
        cp=ftr.add_paragraph(); cp.paragraph_format.space_before=Pt(0); cp.paragraph_format.space_after=Pt(2)
        _run(cp, f"⚠ Data confidence: {caveat}", italic=True, size=7, color=C.concern)
    fp=ftr.add_paragraph(); fp.paragraph_format.space_before=Pt(2); fp.paragraph_format.space_after=Pt(0)
    _run(fp, f"{report_date}    Page ", size=8, color=C.faint)
    r=fp.add_run()
    for tag,txt in [("begin",None),("separate",None),("end",None)]:
        fc=OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"),tag)
        if tag=="begin":
            it=OxmlElement("w:instrText"); it.text="PAGE"; r._r.append(fc); r._r.append(it)
        else: r._r.append(fc)
    r.font.size=Pt(8); r.font.color.rgb=C.faint

def _cover(doc, meta):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(60); p.paragraph_format.space_after=Pt(6)
    r=p.add_run(meta.get("school_name") or "School"); r.bold=True; r.font.size=Pt(28); r.font.color.rgb=C.accent
    if meta.get("school_mission"):
        p2=doc.add_paragraph(); p2.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before=Pt(2); p2.paragraph_format.space_after=Pt(20)
        r2=p2.add_run(meta["school_mission"]); r2.italic=True; r2.font.size=Pt(11); r2.font.color.rgb=C.faint
    div=doc.add_paragraph(); div.paragraph_format.space_before=Pt(0); div.paragraph_format.space_after=Pt(20)
    _bottom_border(div, _hex(C.mid), sz=12)
    t=doc.add_paragraph(); t.alignment=WD_ALIGN_PARAGRAPH.CENTER
    t.paragraph_format.space_before=Pt(0); t.paragraph_format.space_after=Pt(10)
    tr=t.add_run("IT State of the System Report"); tr.bold=True; tr.font.size=Pt(18); tr.font.color.rgb=C.text
    if meta.get("respondent_name") or meta.get("respondent_role"):
        pf=doc.add_paragraph(); pf.alignment=WD_ALIGN_PARAGRAPH.CENTER
        pf.paragraph_format.space_before=Pt(4); pf.paragraph_format.space_after=Pt(2)
        _run(pf,"Prepared for",size=10,color=C.faint)
        if meta.get("respondent_name"):
            pn=doc.add_paragraph(); pn.alignment=WD_ALIGN_PARAGRAPH.CENTER
            pn.paragraph_format.space_before=Pt(2); pn.paragraph_format.space_after=Pt(2)
            _run(pn,meta["respondent_name"],bold=True,size=12)
        if meta.get("respondent_role"):
            pr=doc.add_paragraph(); pr.alignment=WD_ALIGN_PARAGRAPH.CENTER
            pr.paragraph_format.space_before=Pt(0); pr.paragraph_format.space_after=Pt(4)
            _run(pr,meta["respondent_role"],size=10,color=C.faint)
    pd=doc.add_paragraph(); pd.alignment=WD_ALIGN_PARAGRAPH.CENTER
    pd.paragraph_format.space_before=Pt(10)
    _run(pd,meta.get("report_date",date.today().isoformat()),size=9,color=C.faint)

def _exec_summary(doc, meta, summary, findings, scores):
    _page_break(doc); _h(doc,"Executive Summary",1)
    if scores:
        _h(doc,"Section Scores",2)
        tbl=doc.add_table(rows=1,cols=4); tbl.style="Table Grid"
        for i,txt in enumerate(["Section","Score","Status","Answered"]):
            c=tbl.rows[0].cells[i]; _cell_bg(c,_hex(C.accent))
            c.paragraphs[0].clear(); r=c.paragraphs[0].add_run(txt)
            r.bold=True; r.font.size=Pt(9); r.font.color.rgb=C.white
        for idx,s in enumerate(scores):
            row=tbl.add_row().cells; fill="FFFFFF" if idx%2==0 else "F8F9FA"
            for c in row: _cell_bg(c,fill)
            is_ctx=s["max_pts"]==0
            score_txt="Context only" if is_ctx else f"{s['earned']} / {s['max_pts']} ({s['pct']}%)"
            sev_txt="—" if is_ctx else SEV_LABEL.get(s["severity"],s["severity"])
            sev_col=C.faint if is_ctx else SEV_COLOR.get(s["severity"],C.text)
            for c,txt,clr,sz in [(row[0],f"{s['section']['section_id']}. {s['section']['title']}",None,9),
                                  (row[1],score_txt,None,9),(row[2],sev_txt,sev_col,9),(row[3],f"{s['answered_count']} answered",None,9)]:
                c.paragraphs[0].clear(); r=c.paragraphs[0].add_run(txt)
                r.font.size=Pt(sz); r.font.color.rgb=clr or C.text
                if c==row[2]: r.bold=True
        doc.add_paragraph().paragraph_format.space_after=Pt(6)
    _h(doc,"Assessment Overview",2)
    p=_para(doc,sb=4,sa=8)
    _run(p,"This assessment identified "); _run(p,f"{summary['urgent_count']} urgent",bold=True,color=C.urgent)
    _run(p,", "); _run(p,f"{summary['concern_count']} concern",bold=True,color=C.concern)
    _run(p,", and "); _run(p,f"{summary['watch_count']} watch",bold=True,color=C.watch)
    _run(p,f" level findings. {summary['suppressed_count']} findings absorbed into composites (see appendix).")
    mandatory={"F2-C01","F7-C01","F3-C01","F3-C02","F5-C02","F6-C01","F6-C02","F8-C01","F8-008","F9-C01"}
    exec_f=[f for f in findings if f["finding_id"] in mandatory or f["severity"]=="urgent"]
    if exec_f:
        _h(doc,"Priority Findings",2)
        _para(doc,"The following findings require immediate attention or leadership awareness.",size=11,sb=4,sa=8)
        for f in exec_f:
            fill="FDEDEC" if f["severity"]=="urgent" else "FEF9E7"
            def builder(cell,f=f):
                p1=_cp(cell,sb=2,sa=4)
                _run(p1,f"[{SEV_LABEL.get(f['severity'],f['severity'])}]  ",bold=True,size=10,color=SEV_COLOR.get(f["severity"],C.text))
                _run(p1,f["title"],bold=True,size=11)
                _cp(cell,f["description"],size=10,sb=2,sa=2)
                if f.get("notes_passthrough"):
                    p3=_cp(cell,sb=4,sa=2); _run(p3,"IT person noted: ",bold=True,italic=True,size=9,color=C.faint); _run(p3,f["notes_passthrough"],italic=True,size=9)
            _box(doc,fill,builder)

def _key_risks(doc, key_risks, findings):
    _page_break(doc)
    if not key_risks: return
    _h(doc,"Key Risks",1)
    _para(doc,"Named risk groups aggregate related findings. Addressing the primary finding in each group has the broadest impact.",size=11,sb=4,sa=12)
    by_id={f["finding_id"]:f for f in findings}
    for group in sorted(key_risks,key=lambda g:SEV_ORDER.get(g["severity"],9)):
        fill="FDEDEC" if group["severity"]=="urgent" else "FEF9E7" if group["severity"]=="concern" else "FDFEFE"
        def builder(cell,g=group):
            p1=_cp(cell,sb=2,sa=6)
            _run(p1,f"[{SEV_LABEL.get(g['severity'],g['severity'])}]  ",bold=True,size=10,color=SEV_COLOR.get(g["severity"],C.text))
            _run(p1,g["title"],bold=True,size=12)
            for fid in g["finding_ids"]:
                f=by_id.get(fid)
                if not f: continue
                pf=_cp(cell,sb=2,sa=2); pf.paragraph_format.left_indent=Pt(12)
                _run(pf,f"{fid}  ",bold=True,size=9,color=C.faint); _run(pf,f["title"],size=10)
        _box(doc,fill,builder)

def _section_findings(doc, sections_with_findings):
    _page_break(doc); _h(doc,"Section-by-Section Findings",1)
    _para(doc,"Findings ordered by severity within each section. Actions listed under each finding.",size=11,sb=4,sa=12)
    for sec in sections_with_findings:
        _h(doc,f"Section {sec['section_id']}: {sec['section_name']}",2)
        for f in sorted(sec["findings"],key=lambda x:(SEV_ORDER.get(x["severity"],9),x["finding_id"])):
            sev_hex=_hex(SEV_COLOR.get(f["severity"],C.text))
            tp=doc.add_paragraph(); tp.paragraph_format.space_before=Pt(10); tp.paragraph_format.space_after=Pt(4)
            tp.paragraph_format.left_indent=Pt(12); _left_border(tp,sev_hex,sz=20)
            _run(tp,f"[{SEV_LABEL.get(f['severity'],f['severity'])}]  ",bold=True,size=10,color=SEV_COLOR.get(f["severity"],C.text))
            _run(tp,f["title"],bold=True,size=11); _run(tp,f"  {f['finding_id']}",size=8,color=C.faint)
            dp=doc.add_paragraph(); dp.paragraph_format.space_before=Pt(2); dp.paragraph_format.space_after=Pt(6)
            dp.paragraph_format.left_indent=Pt(12); _run(dp,f["description"],size=10)
            if f.get("notes_passthrough"):
                def nb(cell,f=f):
                    p=_cp(cell,sb=2,sa=2); _run(p,"IT person noted: ",bold=True,italic=True,size=9,color=C.faint); _run(p,f["notes_passthrough"],italic=True,size=9)
                _box(doc,"D6EAF8",nb)
            if f.get("plain_language_note"):
                def plb(cell,f=f):
                    p=_cp(cell,sb=2,sa=2); _run(p,"Note: ",bold=True,size=9,color=C.mid); _run(p,f["plain_language_note"],size=9)
                _box(doc,"EBF5FB",plb)
            if f.get("actions"):
                ap=doc.add_paragraph(); ap.paragraph_format.space_before=Pt(4); ap.paragraph_format.space_after=Pt(2)
                ap.paragraph_format.left_indent=Pt(12); _run(ap,"Recommended actions:",bold=True,size=10)
                for act in f["actions"]:
                    lp=doc.add_paragraph(style="List Bullet")
                    lp.paragraph_format.space_before=Pt(2); lp.paragraph_format.space_after=Pt(2); lp.paragraph_format.left_indent=Pt(24)
                    _run(lp,act["description"],size=10)
                    _run(lp,f"  [{HORIZON_LABEL.get(act['time_horizon'],act['time_horizon'])}{'  ⚠ Budget constraint' if act.get('constraint_flag') else ''}]",italic=True,size=9,color=C.faint)
        doc.add_paragraph().paragraph_format.space_after=Pt(8)

def _action_plan(doc, action_buckets):
    _page_break(doc); _h(doc,"Action Plan",1)
    _para(doc,"Actions organised by time horizon, then by section. ⚠ marks budget or staffing constraints.",size=11,sb=4,sa=12)
    for horizon in HORIZON_ORDER:
        bucket=action_buckets.get(horizon,[])
        if not bucket: continue
        _h(doc,HORIZON_LABEL[horizon],2)
        by_sec={}
        for act in bucket:
            by_sec.setdefault(act["section_id"],{"name":act["section_name"],"actions":[]})["actions"].append(act)
        for sid in sorted(by_sec):
            g=by_sec[sid]; _h(doc,f"Section {sid}: {g['name']}",3)
            g["actions"].sort(key=lambda a:SEV_ORDER.get(a["severity"],9))
            for act in g["actions"]:
                lp=doc.add_paragraph(style="List Bullet")
                lp.paragraph_format.space_before=Pt(2); lp.paragraph_format.space_after=Pt(4)
                _run(lp,f"[{act['finding_id']}] ",size=9,color=C.faint)
                _run(lp,("⚠ " if act.get("constraint_flag") else "")+act["description"],size=10)

def _timeline_section(doc, timeline):
    """Render the phased remediation timeline between Action Plan and Appendix."""
    _page_break(doc)
    _h(doc, "Phased Remediation Timeline", 1)
    _para(doc,
          "Effort estimates are based on action complexity ratings (S=0.5d, S+=1d, M=3d, M+=5d, L=10d). "
          "Phase boundaries assume working days and sequential priority. Adjust based on staffing availability.",
          size=10, sb=4, sa=10, color=C.faint)

    SEV_COLOR_MAP = {"urgent": C.urgent, "concern": C.concern, "watch": C.watch}
    EFFORT_LABEL = {"S": "Quick (½ day)", "S+": "Short (1 day)", "M": "Medium (3 days)",
                    "M+": "Substantial (5 days)", "L": "Large (10 days)"}

    for phase in timeline["phases"]:
        acts = phase["actions"]
        if not acts and phase["phase"] in (2, 3, 4):
            continue   # skip empty later phases silently

        # Phase header bar
        fill_hex = {"1": "1A5276", "2": "1F618D", "3": "2471A3", "4": "2E86C1"}.get(str(phase["phase"]), "2C3E50")
        tbl = doc.add_table(rows=1, cols=1); tbl.style = "Table Grid"
        hcell = tbl.rows[0].cells[0]; _cell_bg(hcell, fill_hex); _cell_border(hcell)
        for p in list(hcell.paragraphs): p._element.getparent().remove(p._element)
        hp = hcell.add_paragraph()
        hp.paragraph_format.space_before = Pt(4); hp.paragraph_format.space_after = Pt(4)
        _run(hp, phase["label"], bold=True, size=12, color=C.white)
        if phase["duration_days"] > 0:
            date_str = f"  ·  {phase['start'].strftime('%d %b %Y')} → {phase['end'].strftime('%d %b %Y')}"
            _run(hp, date_str, size=10, color=C.white)
        else:
            _run(hp, f"  ·  Starting {phase['start'].strftime('%d %b %Y')}", size=10, color=C.white)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

        if not acts:
            _para(doc, "No actions in this phase.", size=10, italic=True, color=C.faint, sb=2, sa=8)
        else:
            # Actions table
            at = doc.add_table(rows=1, cols=4); at.style = "Table Grid"
            col_headers = ["Action", "Finding", "Effort", "Severity"]
            for i, txt in enumerate(col_headers):
                c = at.rows[0].cells[i]; _cell_bg(c, "EBF5FB")
                c.paragraphs[0].clear(); r = c.paragraphs[0].add_run(txt)
                r.bold = True; r.font.size = Pt(9); r.font.color.rgb = C.accent
            # Sort: urgent first, then by effort desc
            effort_rank = {"L": 0, "M+": 1, "M": 2, "S+": 3, "S": 4}
            sev_rank = {"urgent": 0, "concern": 1, "watch": 2}
            sorted_acts = sorted(acts, key=lambda a: (
                sev_rank.get(a.get("severity", "watch"), 9),
                effort_rank.get(a.get("effort", "M"), 5),
            ))
            for idx, act in enumerate(sorted_acts):
                row = at.add_row().cells
                fill = "FFFFFF" if idx % 2 == 0 else "F8F9FA"
                for c in row: _cell_bg(c, fill)
                sev_col = SEV_COLOR_MAP.get(act.get("severity", "watch"), C.text)
                effort_txt = EFFORT_LABEL.get(act.get("effort", ""), act.get("effort", "—"))
                for c, txt, col in [
                    (row[0], act["description"], C.text),
                    (row[1], f"{act['finding_id']}", C.faint),
                    (row[2], effort_txt, C.text),
                    (row[3], act.get("severity", "—").upper(), sev_col),
                ]:
                    c.paragraphs[0].clear(); r = c.paragraphs[0].add_run(str(txt))
                    r.font.size = Pt(9); r.font.color.rgb = col
                    if c == row[3]: r.bold = True
            doc.add_paragraph().paragraph_format.space_after = Pt(4)

        # Re-run note
        if phase.get("rerun_note"):
            def rnb(cell, note=phase["rerun_note"]):
                p = _cp(cell, sb=4, sa=4)
                _run(p, note, size=10, color=C.mid)
            _box(doc, "D6EAF8", rnb)
            doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Strategic / future note
    strat = timeline.get("strategic_actions", [])
    if strat:
        _h(doc, "Strategic & Future Actions", 2)
        _para(doc, f"{len(strat)} action(s) are flagged as strategic or multi-year initiatives. "
                   "These are not included in the phased timeline but should be revisited annually.",
              size=10, sb=4, sa=6, color=C.faint)
        for act in strat:
            p = _para(doc, sb=2, sa=2)
            p.paragraph_format.left_indent = Pt(18)
            _run(p, f"[{act['finding_id']}]  ", size=9, color=C.faint)
            _run(p, act["description"], size=10)


def _appendix(doc, suppressed, unknown_log, response_log):
    _page_break(doc); _h(doc,"Appendix",1)
    if suppressed:
        _h(doc,"A. Composite Finding Traceability",2)
        _para(doc,"Findings absorbed into composites — their actions are included in the composite finding.",size=10,sb=4,sa=8)
        for f in suppressed:
            p=_para(doc,sb=2,sa=2); _run(p,f"{f['finding_id']}  ",bold=True,size=9,color=C.faint)
            _run(p,f["title"],size=10); _run(p,f"  → {f['suppressed_by']}",italic=True,size=9,color=C.faint)
        doc.add_paragraph().paragraph_format.space_after=Pt(8)
    if unknown_log:
        _h(doc,"B. Unknown Answer Log",2)
        _para(doc,f"{len(unknown_log)} questions answered as \"I don't know.\" Each is a knowledge gap to investigate.",size=10,sb=4,sa=8)
        by_sec={}
        for u in unknown_log: by_sec.setdefault(u["section_id"],[]).append(u["question_id"])
        for sid in sorted(by_sec):
            p=_para(doc,sb=2,sa=2); p.paragraph_format.left_indent=Pt(18)
            _run(p,f"Section {sid}: ",bold=True,size=10); _run(p,", ".join(by_sec[sid]),size=10)
        doc.add_paragraph().paragraph_format.space_after=Pt(8)
    _h(doc,"C. Full Response Log",2)
    _para(doc,"Complete record of all answers submitted during this assessment.",size=10,sb=4,sa=8)
    tbl=doc.add_table(rows=1,cols=3); tbl.style="Table Grid"
    for i,txt in enumerate(["Question","Status","Answer"]):
        c=tbl.rows[0].cells[i]; _cell_bg(c,_hex(C.accent))
        c.paragraphs[0].clear(); r=c.paragraphs[0].add_run(txt)
        r.bold=True; r.font.size=Pt(9); r.font.color.rgb=C.white
    for idx,r in enumerate(response_log):
        row=tbl.add_row().cells; fill="FFFFFF" if idx%2==0 else "F8F9FA"
        for c in row: _cell_bg(c,fill)
        status_col=C.concern if r["status"]=="unknown" else C.faint if r["status"]=="skipped" else C.text
        for c,txt,col in [(row[0],r["question_id"],C.faint),(row[1],r["status"],status_col),
                          (row[2],(r["answer"] or f"({r['status']})")[:120],C.text)]:
            c.paragraphs[0].clear(); run=c.paragraphs[0].add_run(txt); run.font.size=Pt(8); run.font.color.rgb=col

def generate_report(report_data, answers, profile, section_results=None, start_date=None):
    school_name    =_get(answers,"1.1") or (profile or {}).get("school_name","School")
    school_mission =_get(answers,"1.5")
    respondent_name=_get(answers,"1.7a")
    respondent_role=_get(answers,"1.7b")
    report_date    =date.today().isoformat()
    confidence     =report_data.get("data_confidence","high")
    caveat_map={"moderate":"Most answers are based on recall rather than documented verification. Verify findings before taking action.",
                "low":"Many answers were estimated or unknown. Treat findings as provisional until confirmed.",
                "mixed":"Data confidence varies by section. Verify findings in flagged areas before taking action."}
    confidence_caveat=caveat_map.get(confidence,"")
    meta={"school_name":school_name,"school_mission":school_mission,"respondent_name":respondent_name,
          "respondent_role":respondent_role,"report_date":report_date,"confidence_caveat":confidence_caveat}
    findings=report_data.get("findings",[]); suppressed=report_data.get("suppressed_findings",[])
    key_risks=list(report_data.get("key_risk_groups",{}).values())
    by_sev=report_data.get("by_severity",{})
    summary={"urgent_count":len(by_sev.get("urgent",[])),"concern_count":len(by_sev.get("concern",[])),
             "watch_count":len(by_sev.get("watch",[])),"suppressed_count":len(suppressed),"finding_count":len(findings)}
    sections_map={}
    for f in findings:
        sid=f["section_id"]; sname=SECTION_NAMES.get(sid,f"Section {sid}")
        sections_map.setdefault(sid,{"section_id":sid,"section_name":sname,"findings":[]})["findings"].append(f)
    sections_with_findings=list(sections_map.values())
    action_buckets={h:[] for h in HORIZON_ORDER}
    for f in findings:
        for act in f.get("actions",[]):
            action_buckets[act["time_horizon"]].append({"finding_id":f["finding_id"],"section_id":f["section_id"],
                "section_name":SECTION_NAMES.get(f["section_id"],f"Section {f['section_id']}"),"severity":f["severity"],
                "description":act["description"],"time_horizon":act["time_horizon"],"constraint_flag":act.get("constraint_flag",False)})
    unknown_log=sorted([{"question_id":qid,"section_id":qid.split(".")[0]} for qid,d in answers.items() if d.get("answer_status")=="unknown"],key=lambda x:(x["section_id"],x["question_id"]))
    response_log=sorted([{"question_id":qid,"section_id":qid.split(".")[0],"status":d.get("answer_status","unanswered"),"answer":str(d.get("raw_answer","")) if d.get("raw_answer") else ""} for qid,d in answers.items()],key=lambda x:(x["section_id"],x["question_id"]))
    # Build phased timeline if start_date provided
    timeline = None
    if start_date:
        from timeline import build_timeline
        from datetime import date as _date
        sd = _date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
        timeline = build_timeline(findings, sd)
    doc=Document()
    for sec in doc.sections:
        sec.top_margin=Inches(0.75); sec.bottom_margin=Inches(0.75)
        sec.left_margin=Inches(0.9); sec.right_margin=Inches(0.9)
    _set_hf(doc,school_name,report_date,confidence_caveat)
    _cover(doc,meta)
    _exec_summary(doc,meta,summary,findings,section_results or [])
    _key_risks(doc,key_risks,findings)
    _section_findings(doc,sections_with_findings)
    _action_plan(doc,action_buckets)
    if timeline:
        _timeline_section(doc, timeline)
    _appendix(doc,suppressed,unknown_log,response_log)
    buf=io.BytesIO(); doc.save(buf); buf.seek(0)
    return buf.read()
