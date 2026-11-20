import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import pandas as pd
from typing import List, Dict, Any

class ReportService:
    @staticmethod
    def generate_project_pdf(project: Any, prediction: Dict[str, Any]) -> bytes:
        """Generates a styled executive PDF summary report for a single project's risk analysis."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1A365D"), # Deep Navy
            spaceAfter=10,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            name="SubTitleStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#4A5568"), # Slate Gray
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        section_heading = ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#2B6CB0"), # Slate Blue
            spaceBefore=12,
            spaceAfter=6
        )
        
        body_style = ParagraphStyle(
            name="BodyStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#2D3748")
        )
        
        bullet_style = ParagraphStyle(
            name="BulletStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#2D3748"),
            leftIndent=12,
            spaceAfter=3
        )
        
        story = []
        
        # 1. Header
        story.append(Paragraph("AI Project Success/Failure Prediction System", title_style))
        story.append(Paragraph(f"AI Risk Assessment & Prediction Report — Generated on {project.created_at.strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
        story.append(Spacer(1, 8))
        
        # 2. Project Meta Table
        story.append(Paragraph("Project Metrics Overview", section_heading))
        meta_data = [
            [Paragraph("<b>Project Name:</b>", body_style), Paragraph(project.name, body_style),
             Paragraph("<b>Company:</b>", body_style), Paragraph(project.company_name or "N/A", body_style)],
            [Paragraph("<b>Project Type:</b>", body_style), Paragraph(project.project_type or "Web", body_style),
             Paragraph("<b>Budget:</b>", body_style), Paragraph(f"${project.budget:,.2f}", body_style)],
            [Paragraph("<b>Duration (Days):</b>", body_style), Paragraph(str(project.duration_days), body_style),
             Paragraph("<b>Team Size:</b>", body_style), Paragraph(str(project.team_size), body_style)],
            [Paragraph("<b>Avg Experience (Yrs):</b>", body_style), Paragraph(f"{project.team_experience_years:.1f} yrs", body_style),
             Paragraph("<b>Project Complexity:</b>", body_style), Paragraph(f"{project.project_complexity}/5", body_style)],
            [Paragraph("<b>Testing Coverage:</b>", body_style), Paragraph(f"{project.testing_coverage:.1f}%", body_style),
             Paragraph("<b>Bug Count:</b>", body_style), Paragraph(str(project.bug_count), body_style)],
            [Paragraph("<b>Sprint Delays:</b>", body_style), Paragraph(str(project.sprint_delays), body_style),
             Paragraph("<b>Requirement Changes:</b>", body_style), Paragraph(str(project.requirement_changes), body_style)],
        ]
        
        t_meta = Table(meta_data, colWidths=[120, 140, 120, 140])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('PADDING', (0,0), (-1,-1), 5),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 10))
        
        # 3. Prediction Result Box
        story.append(Paragraph("AI Prediction & Risk Analysis", section_heading))
        
        is_success = prediction["is_successful_prediction"]
        result_text = "✅ SUCCESS PREDICTED" if is_success else "❌ FAILURE PREDICTED"
        bg_color = "#EBF8FF" if is_success else "#FFF5F5"
        text_color = "#2B6CB0" if is_success else "#C53030"
        
        result_style = ParagraphStyle(
            name="ResultStyle",
            parent=styles["Normal"],
            fontSize=12,
            leading=15,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor(text_color),
            alignment=TA_CENTER
        )
        
        pred_data = [
            [Paragraph(result_text, result_style)],
            [Paragraph(
                f"<b>Success Probability:</b> {prediction['success_probability']*100:.1f}% | "
                f"<b>Failure Probability:</b> {prediction['failure_probability']*100:.1f}%<br/>"
                f"<b>Risk Score:</b> {prediction['risk_score']:.1f}/100 (<b>{prediction['risk_level']} Risk</b>) | "
                f"<b>Health Score:</b> {prediction['health_score']:.1f}/100",
                body_style
            )]
        ]
        
        t_pred = Table(pred_data, colWidths=[520])
        t_pred.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
            ('BOX', (0,0), (-1,-1), 1.2, colors.HexColor(text_color)),
            ('PADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        story.append(t_pred)
        story.append(Spacer(1, 10))
        
        # 4. Top Impact Factors
        story.append(Paragraph("Key Drivers & Risk Factors (Explainable AI)", section_heading))
        
        factors_data = [
            [Paragraph("<b>Top Positive Drivers</b> (Pushes towards Success)", body_style),
             Paragraph("<b>Top Risk Factors</b> (Pushes towards Failure)", body_style)]
        ]
        
        pos_list = "<br/>".join([f"• {f}" for f in prediction["top_success_factors"]])
        neg_list = "<br/>".join([f"• {f}" for f in prediction["top_risk_factors"]])
        
        factors_data.append([
            Paragraph(pos_list, body_style),
            Paragraph(neg_list, body_style)
        ])
        
        t_factors = Table(factors_data, colWidths=[260, 260])
        t_factors.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_factors)
        story.append(Spacer(1, 10))
        
        # 5. Recommendations
        story.append(Paragraph("AI Actionable Recommendations", section_heading))
        for rec in prediction["recommendations"]:
            story.append(Paragraph(f"• {rec}", bullet_style))
            story.append(Spacer(1, 2))
            
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_excel_report(projects: List[Any]) -> bytes:
        """Generates a summary Excel spreadsheet for a list of projects and predictions."""
        buffer = io.BytesIO()
        data = []
        for p in projects:
            data.append({
                "Project ID": p.id,
                "Project Name": p.name,
                "Company Name": p.company_name,
                "Project Type": p.project_type,
                "Budget": p.budget,
                "Duration (Days)": p.duration_days,
                "Team Size": p.team_size,
                "Avg Experience (Yrs)": p.team_experience_years,
                "Testing Coverage %": p.testing_coverage,
                "Bugs Count": p.bug_count,
                "Sprint Delays": p.sprint_delays,
                "Requirement Changes": p.requirement_changes,
                "Success Probability": p.success_probability if p.success_probability is not None else 0.0,
                "Risk Score": p.risk_score if p.risk_score is not None else 0.0,
                "Risk Level": p.risk_level or "Unknown",
                "Health Score": p.health_score if p.health_score is not None else 0.0,
                "Archived": p.is_archived,
                "Created At": p.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        df = pd.DataFrame(data)
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Project Predictions")
            
        buffer.seek(0)
        return buffer.getvalue()
