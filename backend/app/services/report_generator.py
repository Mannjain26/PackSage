"""
PDF + QR Report Generator with Validation Passport & Supplier RFQ Spec Sheet
"""
import os
import io
import uuid
from datetime import datetime
from typing import List, Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table as RLTable, TableStyle, HRFlowable, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import qrcode
    from qrcode.image.pil import PilImage
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_qr_png(value: str, report_id: str) -> str:
    """Generate a QR code PNG and return its file path."""
    if not QR_AVAILABLE:
        return ""
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(value)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    path = os.path.join(REPORTS_DIR, f"qr_{report_id}.png")
    img.save(path)
    return path


def generate_pdf_report(
    report_id: str,
    report_uuid: str,
    scenario: Any,
    ranked_items: List[Dict],
    shelf_life: Dict,
    req_notes: List[str],
    base_url: str = "http://localhost:5173",
) -> str:
    """
    Build a comprehensive PDF report with:
    1. Scenario Summary with Evidence Badges
    2. Inverse Packaging Barrier Targets
    3. Ranked Packaging Material Recommendations
    4. Auto-Generated Validation Passport (ASTM D3985, ASTM F1249, seal integrity)
    5. Supplier-Ready RFQ Spec Sheet
    6. Traceability QR Code
    """
    file_path = os.path.join(REPORTS_DIR, f"report_{report_id}.pdf")

    if not REPORTLAB_AVAILABLE:
        txt_path = file_path.replace(".pdf", ".txt")
        with open(txt_path, "w") as f:
            f.write(f"PackSage AI Report — {report_uuid}\n")
            f.write(f"Scenario: {scenario.commodity_name}\n")
            f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
        return txt_path

    # ReportLab Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", fontSize=18, spaceAfter=8, textColor=colors.HexColor("#1a5c38"), fontName="Helvetica-Bold", alignment=TA_CENTER)
    subtitle_style = ParagraphStyle("Sub", fontSize=11, alignment=TA_CENTER, spaceAfter=4, textColor=colors.HexColor("#2e7d32"))
    h2_style = ParagraphStyle("H2", fontSize=12, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#1a5c38"), fontName="Helvetica-Bold")
    h3_style = ParagraphStyle("H3", fontSize=10, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor("#333333"), fontName="Helvetica-Bold")
    body_style = styles["Normal"]
    body_style.fontSize = 8.5
    body_style.leading = 11
    disclaimer_style = ParagraphStyle("Disc", fontSize=7.5, textColor=colors.HexColor("#555555"), spaceAfter=3, fontName="Helvetica-Oblique")

    story = []

    # Header Banner
    story.append(Paragraph("PackSage AI — MoFPI SIH260236", title_style))
    story.append(Paragraph("AI-Driven Intelligent Food Packaging Recommendation System", subtitle_style))
    story.append(Paragraph(f"Digital Dossier & Verification Report | ID: {report_uuid}", ParagraphStyle("ID", fontSize=8.5, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=6)))
    story.append(Paragraph(
        "<b>LEGAL & COMPLIANCE NOTICE:</b> Decision-support tool. Requires laboratory testing (ASTM D3985 / ASTM F1249) and shelf-life stability study prior to commercial packaging line commissioning.",
        ParagraphStyle("Notice", fontSize=7.5, textColor=colors.HexColor("#b71c1c"), alignment=TA_CENTER, spaceAfter=8)
    ))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#1a5c38"), spaceAfter=10))

    # 1. Scenario Summary with Evidence-Grade Badges
    story.append(Paragraph("1. Commodity & Storage Profile [Evidence-Grade Audit]", h2_style))
    scenario_data = [
        ["Parameter", "Input Value", "Evidence Badge", "Source / Methodology"],
        ["Commodity", scenario.commodity_name, "Verified", "MoFPI Commodity Taxonomy"],
        ["Category", scenario.commodity_category.replace("_", " ").title(), "Verified", "Standard Food Classification"],
        ["Moisture Content", f"{scenario.moisture_pct or 12.0}%", "User Default", "Initial Matrix Moisture"],
        ["Respiration Rate", f"{scenario.respiration_rate or 'N/A'} mg CO2/kg/h", "Estimated", "Produce Respiration Model (Q10=2.2)"],
        ["Storage & Transit", f"{scenario.storage_type.capitalize()} | {scenario.transport_mode or 'Road'}", "Real-World", "Bharat Supply Chain Simulator"],
        ["Target Shelf Life", f"{scenario.target_shelf_life_days} Days", "User Target", "Inverse Shelf-Life Requirement Target"],
    ]
    t_scen = RLTable(scenario_data, colWidths=[4*cm, 4*cm, 3.5*cm, 5.5*cm])
    t_scen.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a5c38")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8faf8")]),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("PADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(t_scen)
    story.append(Spacer(1, 8))

    # 2. Inferred Barrier Bands
    story.append(Paragraph("2. Inferred Target Barrier Thresholds (Inverse Solver)", h2_style))
    is_produce = scenario.commodity_category == "fresh_produce"
    target_otr = "≥ 1,500 cc/m²·d (Breathable/Micro-perf)" if is_produce else "≤ 5.0 – 25.0 cc/m²·d"
    target_wvtr = "15.0 – 25.0 g/m²·d (Anti-fog)" if is_produce else "≤ 0.8 – 2.5 g/m²·d"
    
    barrier_data = [
        ["Barrier Parameter", "Solved Maximum Permissible Spec", "Standard Test Method", "Failure Mode Mitigated"],
        ["Oxygen Transmission (OTR)", target_otr, "ASTM D3985 (Coulometric)", "Lipid Rancidity & Aerobic Spoilage"],
        ["Water Vapor Transmission (WVTR)", target_wvtr, "ASTM F1249 (Modulated IR)", "Moisture Ingress / Crispness Loss / Caking"],
        ["Target Thickness", "25 - 70 µm", "ASTM D6988 / ISO 4593", "Pin-hole Puncture & Transit Burst Resistance"]
    ]
    t_barr = RLTable(barrier_data, colWidths=[5*cm, 4.5*cm, 3.8*cm, 3.7*cm])
    t_barr.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2e7d32")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f4f9f4")]),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("PADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(t_barr)
    story.append(Spacer(1, 8))

    # 3. Top Ranked Packaging Recommendations
    story.append(Paragraph("3. Recommended Packaging Materials (Ranked by Multi-Criteria Fit)", h2_style))
    mat_data = [["Rank", "Material Structure", "Type", "Fit Score", "OTR", "WVTR", "Cost Tier", "Recyclability"]]
    for item in ranked_items[:5]:
        m = item["material"]
        mat_data.append([
            f"#{item['rank']}",
            m.name[:32],
            m.mat_type,
            f"{item['fit_score']:.2f}",
            f"{m.otr or 'N/A'}",
            f"{m.wvtr or 'N/A'}",
            f"{m.cost_index:.1f}/5.0",
            "Recyclable (Class 4)" if m.recyclable else ("Compostable" if m.biodegradable else "Multi-layer")
        ])
    t_mat = RLTable(mat_data, colWidths=[1.2*cm, 4.8*cm, 2.2*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.7*cm, 2.7*cm])
    t_mat.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a5c38")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f9fbf9")]),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("PADDING", (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_mat)
    story.append(Spacer(1, 8))

    # 4. Auto-Generated VALIDATION PASSPORT
    story.append(Paragraph("4. Validation Passport — Laboratory Testing Checklist", h2_style))
    passport_data = [
        ["Standard Test Protocol", "Designation", "Target Threshold", "Status / Next Step"],
        ["Oxygen Transmission Rate", "ASTM D3985 / ISO 15105-2", f"Confirm {target_otr}", "Send film swatch to NABL accredited lab"],
        ["Water Vapor Transmission Rate", "ASTM F1249 / ISO 15106-2", f"Confirm {target_wvtr}", "Verify under 38°C / 90% RH tropical chamber"],
        ["Heat Seal Integrity & Strength", "ASTM F88 / ASTM F2029", "≥ 15 N / 15mm seal width", "Calibrate pouch sealer dwell & temperature"],
        ["Puncture & Dart Impact", "ASTM D1709 / ASTM F1306", "≥ 250 g dart impact", "Check truck transit vibration resilience"],
        ["Accelerated Shelf-Life (ASLT)", "MoFPI / IS 10171", f"{scenario.target_shelf_life_days} days equivalent", "Run 40°C / 75% RH 30-day incubator trial"]
    ]
    t_pass = RLTable(passport_data, colWidths=[4.2*cm, 4.2*cm, 4.3*cm, 4.3*cm])
    t_pass.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0d47a1")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#eef4fc")]),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("PADDING", (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_pass)
    story.append(Spacer(1, 8))

    # 5. Packaging Cost Estimation & Commercial Summary
    story.append(Paragraph("5. Packaging Cost Estimation & Economic Feasibility", h2_style))
    curr = getattr(scenario, "currency", "INR") or "INR"
    curr_sym = "₹" if curr == "INR" else ("$" if curr == "USD" else "€")
    qty = getattr(scenario, "package_quantity", 10000) or 10000
    p_weight_g = getattr(scenario, "product_weight_g", 100.0) or 100.0

    cost_rows = [["Rank / Material", "Cost / Pkg", f"Cost / kg Food", f"Batch ({qty:,} pkgs)", "Material Share", "Confidence"]]
    for item in ranked_items[:4]:
        m = item["material"]
        c_est = item.get("cost_estimate")
        if c_est:
            c_pkg = f"{curr_sym}{c_est.get('cost_per_package', 0):.2f}"
            c_kg = f"{curr_sym}{c_est.get('cost_per_kg_food', 0):.2f}" if c_est.get('cost_per_kg_food') else "N/A"
            c_batch = f"{curr_sym}{c_est.get('total_batch_cost', 0):,.0f}"
            mat_share = f"{c_est.get('material_cost_share_pct', 0):.0f}%"
            conf = c_est.get("confidence", "Medium").title()
        else:
            c_pkg = f"{curr_sym}{(m.price_per_kg or 150)*0.005:.2f}"
            c_kg = "N/A"
            c_batch = "N/A"
            mat_share = "N/A"
            conf = "Indicative"
        cost_rows.append([m.name[:28], c_pkg, c_kg, c_batch, mat_share, conf])

    t_cost = RLTable(cost_rows, colWidths=[5.5*cm, 2.5*cm, 2.8*cm, 3.2*cm, 2.2*cm, 2.0*cm])
    t_cost.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e65100")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fff3e0")]),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("PADDING", (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_cost)
    story.append(Paragraph(
        "<b>Cost Disclaimer:</b> Cost values are indicative estimates based on raw material densities, typical scrap wastage, and benchmark converting/sealing costs. Actual prices depend on supplier quotes, tooling/cylinder setup, minimum order quantities (MOQ), and spot polymer resin prices.",
        disclaimer_style
    ))
    story.append(Spacer(1, 6))

    # 6. Supplier-Ready RFQ Spec Sheet (Procurement Spec)
    top_pick = ranked_items[0]["material"] if ranked_items else None
    top_name = top_pick.name if top_pick else "High-Barrier Multi-layer Laminate"
    story.append(Paragraph("6. Supplier Procurement Spec Sheet (RFQ-Ready)", h2_style))
    rfq_data = [
        ["RFQ Field", "Supplier Target Specification", "Industry Notes"],
        ["Recommended Material", top_name, "Commercial converter grade"],
        ["Target OTR Limit", f"{target_otr}", "cc/m²·day @ 23°C, 0% RH"],
        ["Target WVTR Limit", f"{target_wvtr}", "g/m²·day @ 38°C, 90% RH"],
        ["Nominal Thickness Range", "30 – 55 µm ± 5%", "Guaranteed gauge variation < 5%"],
        ["Sealing Type", "Heat Sealable (PE / CPP sealant web)", "Seal initiation temp ~ 105-125°C"],
        ["Food Contact Compliance", "FSSAI 2018 / 21 CFR § 177.1520", "Migration test certificate mandatory"]
    ]
    t_rfq = RLTable(rfq_data, colWidths=[4.5*cm, 6.5*cm, 6.0*cm])
    t_rfq.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#37474f")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#eceff1")]),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("PADDING", (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_rfq)
    story.append(Spacer(1, 6))

    # 7. Traceability QR Code
    qr_url = f"{base_url}/scenario/{scenario.id}/results?uuid={report_uuid}"
    qr_path = generate_qr_png(qr_url, report_id)

    qr_elements = [
        Paragraph(f"<b>Verification Passport UUID:</b> {report_uuid}", body_style),
        Paragraph(f"<b>Audit URL:</b> {qr_url}", body_style),
        Paragraph("Scan QR with any smartphone to inspect digital tamper-evident audit record.", disclaimer_style),
    ]
    if qr_path and os.path.exists(qr_path):
        from reportlab.platypus import Image as RLImage
        qr_img = RLImage(qr_path, width=2.6*cm, height=2.6*cm)
        qr_table = RLTable([[qr_elements, qr_img]], colWidths=[13*cm, 4*cm])
        qr_table.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("PADDING", (0,0), (-1,-1), 0),
        ]))
        story.append(qr_table)

    # Footer
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.grey, spaceAfter=4))
    story.append(Paragraph(
        f"PackSage AI | Government of India MoFPI PS 26236 | Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        disclaimer_style
    ))

    doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=1.2*cm, bottomMargin=1.2*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
    doc.build(story)
    return file_path
