import os
import sys
import glob
from pathlib import Path
from md_to_word import convert_md_to_docx

def compile_market_intelligence_report(input_dir: str = "delivery_pack", output_md: str = "Market_Intelligence_Report.md"):
    input_path = Path(input_dir)
    md_files = sorted(list(input_path.glob("dossier_*.md")))
    
    if not md_files:
        print(f"No dossiers found in {input_dir}")
        return None, None
        
    print(f"Combining {len(md_files)} opportunity dossiers into a single master report...")

    master_content = []
    
    # Master Report Header & Executive Summary
    master_content.append("# Master Market Intelligence Report")
    master_content.append("## Validated B2B SaaS Opportunities & Operational Friction Analysis")
    master_content.append(f"**Date:** October 2026 | **Total Validated Opportunities:** {len(md_files)} | **Source Community:** Reddit (r/smallbusiness)")
    master_content.append("---")
    master_content.append("### Executive Overview")
    master_content.append(
        "This master intelligence brief synthesizes validated operational bottlenecks and recurring commercial friction "
        "mined across small business communities. Each section represents a standalone, qualified venture opportunity "
        "screened through local System 1 decision gating and deep product synthesis."
    )
    master_content.append("")
    master_content.append("### Table of Opportunities")
    
    # Build Table of Contents
    for idx, md_file in enumerate(md_files, 1):
        with open(md_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        title = md_file.stem.replace("dossier_", "").replace("_", " ")
        for line in lines:
            if line.startswith("# "):
                title = line.replace("# ", "").replace("Opportunity Dossier: ", "").strip()
                break
        master_content.append(f"{idx}. **Opportunity {idx}:** {title}")
        
    master_content.append("")
    master_content.append("---")
    master_content.append("")

    # Append each individual dossier
    for idx, md_file in enumerate(md_files, 1):
        with open(md_file, "r", encoding="utf-8") as f:
            raw = f.read()
            
        # Strip frontmatter if present
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                raw = parts[2].strip()
                
        # Demote H1 to H2 so the master report retains top-level hierarchy
        section_lines = []
        for line in raw.split("\n"):
            if line.startswith("# "):
                section_lines.append(f"## Opportunity {idx}: " + line[2:])
            elif line.startswith("## "):
                section_lines.append("### " + line[3:])
            elif line.startswith("### "):
                section_lines.append("#### " + line[4:])
            else:
                section_lines.append(line)
                
        master_content.append("\n".join(section_lines))
        master_content.append("")
        master_content.append("---")
        master_content.append("")

    out_md_path = input_path / output_md
    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(master_content))
        
    print(f"✅ Master Markdown written to: {out_md_path}")
    
    # Convert to single master Word document
    out_docx_path = out_md_path.with_suffix(".docx")
    convert_md_to_docx(str(out_md_path), str(out_docx_path))
    print(f"✅ Master Word Document written to: {out_docx_path}")
    
    return str(out_md_path), str(out_docx_path)

if __name__ == "__main__":
    compile_market_intelligence_report()
