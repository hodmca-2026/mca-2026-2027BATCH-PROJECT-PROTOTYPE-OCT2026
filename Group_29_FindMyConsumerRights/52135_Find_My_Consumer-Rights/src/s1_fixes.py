import os
import re
import json
import csv
import pdfplumber

base_dir = r"c:\Users\kisho\OneDrive\Desktop\IR_Project_Consumer-Rights"
raw_dir = os.path.join(base_dir, 'data', 'raw')
processed_dir = os.path.join(base_dir, 'data', 'processed')

def clean_text(t):
    t = t.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    t = re.sub(r'([a-z])\.([A-Z])', r'\1. \2', t)
    t = re.sub(r'\bPage \d+ of \d+\b', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\[\d+\]', '', t)
    return t

def get_pdf_text(filename):
    path = os.path.join(raw_dir, filename)
    with pdfplumber.open(path) as pdf:
        pages_text = []
        for p in pdf.pages:
            # Filter out Helvetica-Bold watermark characters for the Act PDF
            if filename == "CONSUMER RIGHTS A2019-35.pdf":
                clean_p = p.filter(lambda obj: obj.get('object_type') != 'char' or obj.get('fontname') != 'Helvetica-Bold')
            else:
                clean_p = p
            txt = clean_p.extract_text()
            if txt:
                pages_text.append(txt)
        raw_text = '\n'.join(pages_text)

    # Filter Devanagari and gazette headers
    lines = raw_text.split('\n')
    english_lines = []
    for line in lines:
        if len(re.findall(r'[\u0900-\u097F]', line)) == 0:
            if "THE GAZETTE OF INDIA" in line or "EXTRAORDINARY" in line or "PART II" in line:
                continue
            if "Uploaded by Dte. of Printing" in line or "Published by the Controller of Publications" in line:
                continue
            if re.match(r'^\[F\. No\.|^\[फा\.सं\.', line) or re.match(r'^\d+$', line.strip()):
                continue
            english_lines.append(line)
    return '\n'.join(english_lines)

def extract_title(text, num_str):
    m = re.search(rf'^{num_str}\.\s*(.*?)(?:\.—|\.\s*–|\.-|\.\s*-)', text)
    if m:
        return m.group(1).strip()
    return ""

def parse_cpa():
    text = get_pdf_text("CONSUMER RIGHTS A2019-35.pdf")
    start_idx = text.find("BE it enacted by Parliament")
    if start_idx != -1:
        text = text[start_idx:]
    text = clean_text(text)
    
    positions = []
    for i in range(1, 108):
        match = re.search(rf'\n{i}\.\s', text)
        if match:
            positions.append((i, match.start()))
        else:
            match = re.search(rf'^{i}\.\s', text, re.MULTILINE)
            if match:
                positions.append((i, match.start()))
                
    positions.sort(key=lambda x: x[1])
    passages = []
    
    for idx, (sec_num, pos) in enumerate(positions):
        next_pos = positions[idx+1][1] if idx + 1 < len(positions) else len(text)
        sec_text = text[pos:next_pos].strip()
        title = extract_title(sec_text, str(sec_num))
        breadcrumb = f"Consumer Protection Act 2019 | Section {sec_num} {title}".strip()
        
        if sec_num == 2:
            cl_positions = []
            for cl in range(1, 48):
                cl_match = re.search(rf'\n\({cl}\)\s', sec_text)
                if cl_match:
                    cl_positions.append((cl, cl_match.start()))
                else:
                    cl_match = re.search(rf'^\({cl}\)\s', sec_text, re.MULTILINE)
                    if cl_match:
                        cl_positions.append((cl, cl_match.start()))
            cl_positions.sort(key=lambda x: x[1])
            lead_in = sec_text[:cl_positions[0][1]].strip() if cl_positions else ""
            
            for c_idx, (cl_num, c_pos) in enumerate(cl_positions):
                c_next = cl_positions[c_idx+1][1] if c_idx + 1 < len(cl_positions) else len(sec_text)
                cl_text = sec_text[c_pos:c_next].strip()
                
                if cl_num == 47:
                    sub_positions = []
                    for s in ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix']:
                        s_match = re.search(rf'\n\({s}\)\s', cl_text)
                        if s_match:
                            sub_positions.append((s, s_match.start()))
                        else:
                            s_match = re.search(rf'^\({s}\)\s', cl_text, re.MULTILINE)
                            if s_match:
                                sub_positions.append((s, s_match.start()))
                    sub_positions.sort(key=lambda x: x[1])
                    cl_lead_in = cl_text[:sub_positions[0][1]].strip() if sub_positions else ""
                    for s_idx, (s_num, s_pos) in enumerate(sub_positions):
                        s_next = sub_positions[s_idx+1][1] if s_idx + 1 < len(sub_positions) else len(cl_text)
                        s_text = cl_text[s_pos:s_next].strip()
                        bc = f"Consumer Protection Act 2019 | Section 2(47)({s_num})"
                        passages.append({
                            "passage_id": f"CPA_s2_47_{s_num}",
                            "text": f"{lead_in} {cl_lead_in} {s_text}".strip(),
                            "metadata": {"doc": "CPA", "breadcrumb": bc}
                        })
                else:
                    bc = f"Consumer Protection Act 2019 | Section 2({cl_num})"
                    passages.append({
                        "passage_id": f"CPA_s2_{cl_num}",
                        "text": f"{lead_in} {cl_text}".strip(),
                        "metadata": {"doc": "CPA", "breadcrumb": bc}
                    })
        else:
            meta = {"doc": "CPA", "breadcrumb": breadcrumb}
            if sec_num in [34, 47, 58]:
                meta["superseded"] = "superseded by Jurisdiction Rules 2021"
            passages.append({
                "passage_id": f"CPA_s{sec_num}",
                "text": sec_text,
                "metadata": meta
            })
            
    return passages

def parse_ecr():
    text = get_pdf_text("E commerce rules_1732703966.pdf")
    start_idx = text.find("MINISTRY OF CONSUMER AFFAIRS")
    if start_idx != -1:
        text = text[start_idx:]
    text = clean_text(text)
    
    rule_titles = {
        1: "Short title and commencement",
        2: "Scope and applicability",
        3: "Definitions",
        4: "Duties of e-commerce entities",
        5: "Liabilities of marketplace e-commerce entities",
        6: "Duties of sellers on marketplace",
        7: "Duties and liabilities of inventory e-commerce entities",
        8: "Contravention of rules"
    }
    
    rule_positions = []
    for r in range(1, 9):
        m = re.search(rf'(?:^|\n)\s*{r}\.\s*', text)
        if m:
            rule_positions.append((r, m.start()))
    rule_positions.sort(key=lambda x: x[1])
    
    passages = []
    for idx, (r_num, pos) in enumerate(rule_positions):
        next_pos = rule_positions[idx+1][1] if idx + 1 < len(rule_positions) else len(text)
        r_text = text[pos:next_pos].strip()
        title = rule_titles.get(r_num, extract_title(r_text, str(r_num)))
        bc_prefix = f"E-Commerce Rules 2020 | Rule {r_num} {title}"
        
        if r_num == 8:
            passages.append({
                "passage_id": "ECR_r8",
                "text": r_text,
                "metadata": {"doc": "ECR", "breadcrumb": bc_prefix}
            })
            continue
            
        max_sr = {1: 2, 2: 2, 3: 2, 4: 11, 5: 5, 6: 5, 7: 5}[r_num]
        sr_positions = []
        for sr in range(1, max_sr + 1):
            patterns = [
                rf'(?:—|–|-|\.-|\.—|---)\s*\({sr}\)\s+',
                rf'\n\s*\({sr}\)\s+',
                rf'^\s*\({sr}\)\s+'
            ]
            found_pos = -1
            for pat in patterns:
                m = re.search(pat, r_text)
                if m:
                    sub_m = re.search(rf'\({sr}\)', r_text[m.start():m.end()])
                    if sub_m:
                        found_pos = m.start() + sub_m.start()
                        break
            if found_pos != -1:
                sr_positions.append((sr, found_pos))
                
        sr_positions.sort(key=lambda x: x[1])
        for s_idx, (sr_num, sp) in enumerate(sr_positions):
            sp_end = sr_positions[s_idx+1][1] if s_idx + 1 < len(sr_positions) else len(r_text)
            sub_text = r_text[sp:sp_end].strip()
            bc = f"{bc_prefix} ({sr_num})"
            passages.append({
                "passage_id": f"ECR_r{r_num}_{sr_num}",
                "text": sub_text,
                "metadata": {"doc": "ECR", "breadcrumb": bc}
            })
    return passages


def parse_dp():
    text = get_pdf_text("The Guidelines for Prevention and Regulation of Dark Patterns, 2023_1732707717.pdf")
    text = clean_text(text)
    
    passages = []
    paras = []
    for p in range(1, 8):
        m = re.search(rf'\n{p}\.\s', text)
        if not m:
            m = re.search(rf'^{p}\.\s', text, re.MULTILINE)
        if m:
            paras.append((p, m.start()))
    
    annex = text.find("ANNEXURE 1")
    if annex != -1:
        paras.append((999, annex))
        
    paras.sort(key=lambda x: x[1])
    for idx, (p_num, pos) in enumerate(paras):
        n_pos = paras[idx+1][1] if idx+1 < len(paras) else len(text)
        p_text = text[pos:n_pos].strip()
        
        if p_num == 999:
            ap = []
            for a in range(1, 14):
                m = re.search(rf'\n\({a}\)\s', p_text)
                if not m:
                    m = re.search(rf'^\({a}\)\s', p_text, re.MULTILINE)
                if m:
                    ap.append((a, m.start()))
            ap.sort(key=lambda x: x[1])
            for a_idx, (a_num, ap_pos) in enumerate(ap):
                an = ap[a_idx+1][1] if a_idx+1 < len(ap) else len(p_text)
                txt = p_text[ap_pos:an].strip()
                name = txt.split("means")[0].split(".-")[0].replace('\n', ' ').strip()
                if a_num == 2: name = '(2) "Basket sneaking"'
                if a_num == 8: name = '(8) "Drip pricing"'
                bc = f"Dark Patterns Guidelines 2023 | Annexure 1 {name}"
                passages.append({"passage_id": f"DP_annex_{a_num}", "text": txt, "metadata": {"doc": "DP", "breadcrumb": bc}})
        else:
            bc = f"Dark Patterns Guidelines 2023 | Paragraph {p_num}"
            passages.append({"passage_id": f"DP_p{p_num}", "text": p_text, "metadata": {"doc": "DP", "breadcrumb": bc}})
    return passages

def parse_jr():
    text = get_pdf_text("Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021.pdf")
    start_idx = text.find("MINISTRY OF CONSUMER AFFAIRS")
    if start_idx != -1:
        text = text[start_idx:]
    text = clean_text(text)
    
    passages = []
    rules = []
    for r in range(3, 6):
        m = re.search(rf'\n{r}\.\s', text)
        if not m:
            m = re.search(rf'^{r}\.\s', text, re.MULTILINE)
        if m:
            rules.append((r, m.start()))
    rules.sort(key=lambda x: x[1])
    for idx, (r_num, pos) in enumerate(rules):
        n_pos = rules[idx+1][1] if idx+1 < len(rules) else len(text)
        txt = text[pos:n_pos].strip()
        title = extract_title(txt, str(r_num))
        bc = f"Jurisdiction Rules 2021 | Rule {r_num} {title}".strip()
        passages.append({"passage_id": f"JR_r{r_num}", "text": txt, "metadata": {"doc": "JR", "breadcrumb": bc}})
    return passages

def parse_mag():
    txt_path = os.path.join(raw_dir, 'Misleading_Ads_Guidelines_2022_OCR.txt')
    if not os.path.exists(txt_path):
        return []
    with open(txt_path, "r", encoding="cp1252") as f:
        raw_content = f.read()

    # Track corrections
    applied_corrections = []
    
    # Specific OCR corrections for (l) -> (1) where (l) represents numeral 1
    # Note: Letter (l) in Section 8 (Children targeted advertisements) is legitimate and not changed
    replacements = [
        ("commencement.(l)", "commencement.(1)", "OCR typo: '(l)' -> '(1)' in Section 1(1)"),
        ("Definitions.(l)", "Definitions.(1)", "OCR typo: '(l)' -> '(1)' in Section 2(1)"),
        ("valid advertisement.(l)", "valid advertisement.(1)", "OCR typo: '(l)' -> '(1)' in Section 4(1)"),
        ("sub-paragraph (l )", "sub-paragraph (1)", "OCR typo: '(l )' -> '(1)' in Section 4(2)"),
        ("targeted advertisements.(l)", "targeted advertisements.(1)", "OCR typo: '(l)' -> '(1)' in Section 8(1)"),
        ("Disclaimers in Advertisements.(l)", "Disclaimers in Advertisements.(1)", "OCR typo: '(l)' -> '(1)' in Section 11(1)"),
        ("endorsement of advertisements.(l)", "endorsement of advertisements.(1)", "OCR typo: '(l)' -> '(1)' in Section 13(1)"),
    ]

    text = raw_content
    for before_str, after_str, reason in replacements:
        if before_str in text:
            text = text.replace(before_str, after_str)
            applied_corrections.append(('Misleading_Ads_Guidelines_2022_OCR.txt', before_str, after_str, reason))

    # Write corrections.csv
    with open(os.path.join(processed_dir, 'corrections.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'before', 'after', 'reason'])
        for row in applied_corrections:
            writer.writerow(row)

    # Footnote line pattern
    footnote_text = (
        "I. Central Consumer Protection Authority, Noti. No. F. No. J-25/4/2020- CCPA (Reg), dated June 9,\n"
        "2022 and published in the Gazette of India, Extra., Part Ill, Section 4, dated 9th June, 2022, pp. 6-11, No. 291"
    )

    # Find section positions
    secs = []
    for s in range(1, 16):
        m = re.search(rf'\n\s*{s}\.\s', text)
        if not m:
            m = re.search(rf'^\s*{s}\.\s', text, re.MULTILINE)
        if m:
            secs.append((s, m.start()))
    secs.sort(key=lambda x: x[1])

    passages = []
    for idx, (s_num, pos) in enumerate(secs):
        n_pos = secs[idx+1][1] if idx+1 < len(secs) else len(text)
        sec_raw = text[pos:n_pos].strip()

        stripped_markers = []
        stripped_footnotes = []

        # Strip page markers like [151], [152], 153, 155
        # Check for [151] or [152]
        bracket_markers = re.findall(r'\[\d+\]', sec_raw)
        if bracket_markers:
            stripped_markers.extend(bracket_markers)
            sec_raw = re.sub(r'\[\d+\]', '', sec_raw)

        # Check for bare page numbers on their own lines: 153, 155
        bare_markers = re.findall(r'^\s*(\d{3})\s*$', sec_raw, re.MULTILINE)
        if bare_markers:
            stripped_markers.extend(bare_markers)
            sec_raw = re.sub(r'^\s*\d{3}\s*\n?', '', sec_raw, flags=re.MULTILINE)

        # Check for gazette footnote
        if "Central Consumer Protection Authority, Noti" in sec_raw:
            fn_match = re.search(r'I\.\s*Central Consumer Protection Authority,.*?\n.*?No\.\s*291', sec_raw, re.DOTALL)
            if fn_match:
                stripped_footnotes.append(fn_match.group(0).strip())
                sec_raw = sec_raw[:fn_match.start()] + sec_raw[fn_match.end():]

        sec_clean = clean_text(sec_raw).strip()
        # Ensure single whitespace formatting
        sec_clean = re.sub(r'\n\s*\n\s*\n+', '\n\n', sec_clean)

        title = extract_title(sec_clean, str(s_num))
        bc = f"Misleading Advertisements Guidelines 2022 | Section {s_num} {title}".strip()
        
        meta = {"doc": "MAG", "breadcrumb": bc}
        if stripped_markers:
            meta["page_markers"] = stripped_markers
        if stripped_footnotes:
            meta["footnotes"] = stripped_footnotes

        passages.append({
            "passage_id": f"MAG_s{s_num}",
            "text": sec_clean,
            "metadata": meta
        })

    return passages

def main():
    passages = parse_cpa() + parse_ecr() + parse_dp() + parse_jr() + parse_mag()
    
    with open(os.path.join(processed_dir, "passages.jsonl"), "w", encoding="utf-8") as f:
        for p in passages:
            f.write(json.dumps(p) + "\n")
            
    print(f"Parsed total {len(passages)} passages into passages.jsonl")

if __name__ == "__main__":
    main()
