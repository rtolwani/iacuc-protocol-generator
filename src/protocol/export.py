"""
Protocol Export Module.

Exports IACUC protocols to PDF and Word formats.
"""

import io
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from src.protocol.schema import Protocol, HumaneEndpoint, DrugInfo, ProcedureInfo


# ============================================================================
# PDF EXPORT
# ============================================================================

class PDFExporter:
    """Exports protocols to PDF format."""
    
    def __init__(
        self,
        institution_name: str = "University Research Institution",
        institution_logo: Optional[Path] = None,
    ):
        self.institution_name = institution_name
        self.institution_logo = institution_logo
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Set up custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.darkblue,
        ))
        
        self.styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
        ))
        
        self.styles.add(ParagraphStyle(
            name='FieldValue',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
        ))
    
    def _add_header(self, story: list, protocol: Protocol):
        """Add header to the document."""
        # Institution name
        story.append(Paragraph(
            self.institution_name,
            self.styles['Title']
        ))
        
        story.append(Paragraph(
            "Institutional Animal Care and Use Committee",
            self.styles['Heading3']
        ))
        
        story.append(Spacer(1, 0.25 * inch))
        
        # Protocol title and number
        story.append(Paragraph(
            f"IACUC Protocol Application",
            self.styles['Heading1']
        ))
        
        if protocol.protocol_number:
            story.append(Paragraph(
                f"Protocol Number: {protocol.protocol_number}",
                self.styles['Normal']
            ))
        
        story.append(Paragraph(
            f"Status: {protocol.status.value.upper()}",
            self.styles['Normal']
        ))
        
        story.append(Spacer(1, 0.25 * inch))
    
    def _add_section(
        self,
        story: list,
        title: str,
        content: list[tuple[str, str]],
    ):
        """Add a section with label-value pairs."""
        story.append(Paragraph(title, self.styles['SectionTitle']))
        
        for label, value in content:
            if value:
                story.append(Paragraph(f"{label}:", self.styles['FieldLabel']))
                story.append(Paragraph(str(value), self.styles['FieldValue']))
                story.append(Spacer(1, 0.1 * inch))
    
    def _add_table(
        self,
        story: list,
        title: str,
        headers: list[str],
        rows: list[list[str]],
    ):
        """Add a table to the document."""
        story.append(Paragraph(title, self.styles['SectionTitle']))
        
        if not rows:
            story.append(Paragraph("None specified", self.styles['FieldValue']))
            return
        
        data = [headers] + rows
        
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.15 * inch))
    
    def export(self, protocol: Protocol, output_path: Optional[Path] = None) -> bytes:
        """
        Export protocol to PDF.
        
        Args:
            protocol: The protocol to export
            output_path: Optional path to save PDF
            
        Returns:
            PDF bytes.
        """
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        
        story = []
        
        # Header
        self._add_header(story, protocol)
        
        # Section 1: General Information
        self._add_section(story, "1. General Information", [
            ("Protocol Title", protocol.title),
            ("Principal Investigator", protocol.principal_investigator.name),
            ("PI Email", protocol.principal_investigator.email),
            ("Department", protocol.department),
            ("Funding Sources", ", ".join(protocol.funding_sources) if protocol.funding_sources else "None specified"),
            ("Study Duration", protocol.study_duration),
        ])
        
        # Section 2: Lay Summary
        self._add_section(story, "2. Lay Summary", [
            ("Summary", protocol.lay_summary),
        ])
        
        # Section 3: Personnel
        if protocol.personnel:
            personnel_rows = [
                [p.name, p.role, ", ".join(p.qualifications) if p.qualifications else "N/A"]
                for p in protocol.personnel
            ]
            self._add_table(
                story,
                "3. Personnel",
                ["Name", "Role", "Qualifications"],
                personnel_rows,
            )
        
        # Section 4: Species and Animal Numbers
        animal_rows = [
            [a.species, a.strain or "N/A", a.sex, str(a.total_number), a.source]
            for a in protocol.animals
        ]
        self._add_table(
            story,
            "4. Species and Animal Numbers",
            ["Species", "Strain", "Sex", "Number", "Source"],
            animal_rows,
        )
        
        self._add_section(story, "", [
            ("USDA Pain Category", protocol.usda_category.value),
            ("Total Animals", str(protocol.total_animals)),
            ("Justification", protocol.animal_number_justification),
        ])
        
        story.append(PageBreak())
        
        # Section 5: Rationale
        self._add_section(story, "5. Rationale and Scientific Justification", [
            ("Scientific Objectives", protocol.scientific_objectives),
            ("Scientific Rationale", protocol.scientific_rationale),
            ("Potential Benefits", protocol.potential_benefits),
        ])
        
        # Section 6: Alternatives (3Rs)
        self._add_section(story, "6. Alternatives (3Rs)", [
            ("Replacement", protocol.replacement_statement),
            ("Reduction", protocol.reduction_statement),
            ("Refinement", protocol.refinement_statement),
        ])
        
        # Section 7: Experimental Design
        self._add_section(story, "7. Experimental Design", [
            ("Design Description", protocol.experimental_design),
            ("Statistical Methods", protocol.statistical_methods),
            ("Power Analysis", protocol.power_analysis),
        ])
        
        # Section 8: Procedures
        if protocol.procedures:
            proc_rows = [
                [p.name, p.description[:100] + "..." if len(p.description) > 100 else p.description]
                for p in protocol.procedures
            ]
            self._add_table(
                story,
                "8. Procedures",
                ["Procedure", "Description"],
                proc_rows,
            )
        
        story.append(PageBreak())
        
        # Section 9: Anesthesia and Analgesia
        if protocol.anesthesia_protocols:
            anes_rows = [
                [d.drug_name, d.dose, d.route, d.purpose]
                for d in protocol.anesthesia_protocols
            ]
            self._add_table(
                story,
                "9. Anesthesia and Analgesia",
                ["Drug", "Dose", "Route", "Purpose"],
                anes_rows,
            )
        
        if protocol.analgesia_protocols:
            analg_rows = [
                [d.drug_name, d.dose, d.route, d.purpose]
                for d in protocol.analgesia_protocols
            ]
            self._add_table(
                story,
                "Analgesia",
                ["Drug", "Dose", "Route", "Purpose"],
                analg_rows,
            )
        
        # Section 10: Surgical Procedures
        if protocol.surgical_procedures:
            self._add_section(story, "10. Surgical Procedures", [
                ("Aseptic Technique", protocol.aseptic_technique),
                ("Post-operative Care", protocol.post_operative_care),
            ])
        
        # Section 11: Humane Endpoints
        if protocol.humane_endpoints:
            endpoint_rows = [
                [e.criterion, e.threshold, e.action]
                for e in protocol.humane_endpoints
            ]
            self._add_table(
                story,
                "11. Humane Endpoints",
                ["Criterion", "Threshold", "Action"],
                endpoint_rows,
            )
        
        self._add_section(story, "", [
            ("Monitoring Schedule", protocol.monitoring_schedule),
        ])
        
        # Section 12: Euthanasia
        self._add_section(story, "12. Euthanasia", [
            ("Primary Method", protocol.euthanasia_method),
            ("Secondary Method", protocol.secondary_method),
            ("AVMA Compliant", "Yes" if protocol.avma_compliant else "No"),
        ])
        
        # Section 13: Hazardous Materials
        self._add_section(story, "13. Hazardous Materials", [
            ("Biohazard Level", protocol.biohazard_level or "None"),
            ("Radiation Use", "Yes" if protocol.radiation_use else "No"),
            ("IBC Approval", protocol.ibc_approval or "N/A"),
        ])
        
        # Footer
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['Normal']
        ))
        
        # Build PDF
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        if output_path:
            output_path.write_bytes(pdf_bytes)
        
        return pdf_bytes


# ============================================================================
# WORD EXPORT (Markdown-based for simplicity)
# ============================================================================

class MarkdownExporter:
    """Exports protocols to Markdown format (can be converted to Word)."""
    
    def __init__(
        self,
        institution_name: str = "University Research Institution",
    ):
        self.institution_name = institution_name
    
    def export(self, protocol: Protocol, output_path: Optional[Path] = None) -> str:
        """
        Export protocol to Markdown.
        
        Args:
            protocol: The protocol to export
            output_path: Optional path to save file
            
        Returns:
            Markdown string.
        """
        lines = []
        
        # Header
        lines.append(f"# {self.institution_name}")
        lines.append("## Institutional Animal Care and Use Committee")
        lines.append("")
        lines.append("# IACUC Protocol Application")
        lines.append("")
        
        if protocol.protocol_number:
            lines.append(f"**Protocol Number:** {protocol.protocol_number}")
        lines.append(f"**Status:** {protocol.status.value.upper()}")
        lines.append("")
        
        # Section 1
        lines.append("## 1. General Information")
        lines.append("")
        lines.append(f"**Protocol Title:** {protocol.title}")
        lines.append(f"**Principal Investigator:** {protocol.principal_investigator.name}")
        lines.append(f"**PI Email:** {protocol.principal_investigator.email or 'N/A'}")
        lines.append(f"**Department:** {protocol.department}")
        lines.append(f"**Funding Sources:** {', '.join(protocol.funding_sources) if protocol.funding_sources else 'None specified'}")
        lines.append(f"**Study Duration:** {protocol.study_duration}")
        lines.append("")
        
        # Section 2
        lines.append("## 2. Lay Summary")
        lines.append("")
        lines.append(protocol.lay_summary)
        lines.append("")
        
        # Section 3
        lines.append("## 3. Personnel")
        lines.append("")
        if protocol.personnel:
            lines.append("| Name | Role | Qualifications |")
            lines.append("|------|------|----------------|")
            for p in protocol.personnel:
                quals = ", ".join(p.qualifications) if p.qualifications else "N/A"
                lines.append(f"| {p.name} | {p.role} | {quals} |")
        else:
            lines.append("*No additional personnel specified*")
        lines.append("")
        
        # Section 4
        lines.append("## 4. Species and Animal Numbers")
        lines.append("")
        lines.append("| Species | Strain | Sex | Number | Source |")
        lines.append("|---------|--------|-----|--------|--------|")
        for a in protocol.animals:
            lines.append(f"| {a.species} | {a.strain or 'N/A'} | {a.sex} | {a.total_number} | {a.source} |")
        lines.append("")
        lines.append(f"**USDA Pain Category:** {protocol.usda_category.value}")
        lines.append(f"**Total Animals:** {protocol.total_animals}")
        lines.append("")
        lines.append("**Justification for Animal Numbers:**")
        lines.append(protocol.animal_number_justification)
        lines.append("")
        
        # Section 5
        lines.append("## 5. Rationale and Scientific Justification")
        lines.append("")
        lines.append("**Scientific Objectives:**")
        lines.append(protocol.scientific_objectives)
        lines.append("")
        lines.append("**Scientific Rationale:**")
        lines.append(protocol.scientific_rationale)
        lines.append("")
        lines.append("**Potential Benefits:**")
        lines.append(protocol.potential_benefits)
        lines.append("")
        
        # Section 6
        lines.append("## 6. Alternatives (3Rs)")
        lines.append("")
        lines.append("**Replacement:**")
        lines.append(protocol.replacement_statement)
        lines.append("")
        lines.append("**Reduction:**")
        lines.append(protocol.reduction_statement)
        lines.append("")
        lines.append("**Refinement:**")
        lines.append(protocol.refinement_statement)
        lines.append("")
        
        # Section 7
        lines.append("## 7. Experimental Design")
        lines.append("")
        lines.append("**Design Description:**")
        lines.append(protocol.experimental_design)
        lines.append("")
        lines.append("**Statistical Methods:**")
        lines.append(protocol.statistical_methods)
        lines.append("")
        if protocol.power_analysis:
            lines.append("**Power Analysis:**")
            lines.append(protocol.power_analysis)
            lines.append("")
        
        # Section 8
        lines.append("## 8. Procedures")
        lines.append("")
        for proc in protocol.procedures:
            lines.append(f"### {proc.name}")
            lines.append(proc.description)
            if proc.frequency:
                lines.append(f"- **Frequency:** {proc.frequency}")
            if proc.anesthesia_required:
                lines.append(f"- **Anesthesia:** {proc.anesthesia_protocol or 'Required'}")
            lines.append("")
        
        # Section 9
        lines.append("## 9. Anesthesia and Analgesia")
        lines.append("")
        if protocol.anesthesia_protocols:
            lines.append("### Anesthesia")
            lines.append("| Drug | Dose | Route | Purpose |")
            lines.append("|------|------|-------|---------|")
            for d in protocol.anesthesia_protocols:
                lines.append(f"| {d.drug_name} | {d.dose} | {d.route} | {d.purpose} |")
            lines.append("")
        
        if protocol.analgesia_protocols:
            lines.append("### Analgesia")
            lines.append("| Drug | Dose | Route | Purpose |")
            lines.append("|------|------|-------|---------|")
            for d in protocol.analgesia_protocols:
                lines.append(f"| {d.drug_name} | {d.dose} | {d.route} | {d.purpose} |")
            lines.append("")
        
        # Section 10
        if protocol.surgical_procedures:
            lines.append("## 10. Surgical Procedures")
            lines.append("")
            if protocol.aseptic_technique:
                lines.append("**Aseptic Technique:**")
                lines.append(protocol.aseptic_technique)
                lines.append("")
            if protocol.post_operative_care:
                lines.append("**Post-operative Care:**")
                lines.append(protocol.post_operative_care)
                lines.append("")
        
        # Section 11
        lines.append("## 11. Humane Endpoints")
        lines.append("")
        if protocol.humane_endpoints:
            lines.append("| Criterion | Threshold | Action |")
            lines.append("|-----------|-----------|--------|")
            for e in protocol.humane_endpoints:
                lines.append(f"| {e.criterion} | {e.threshold} | {e.action} |")
            lines.append("")
        lines.append(f"**Monitoring Schedule:** {protocol.monitoring_schedule}")
        lines.append("")
        
        # Section 12
        lines.append("## 12. Euthanasia")
        lines.append("")
        lines.append(f"**Primary Method:** {protocol.euthanasia_method}")
        if protocol.secondary_method:
            lines.append(f"**Secondary Method:** {protocol.secondary_method}")
        lines.append(f"**AVMA Compliant:** {'Yes' if protocol.avma_compliant else 'No'}")
        lines.append("")
        
        # Section 13
        lines.append("## 13. Hazardous Materials")
        lines.append("")
        lines.append(f"**Biohazard Level:** {protocol.biohazard_level or 'None'}")
        lines.append(f"**Radiation Use:** {'Yes' if protocol.radiation_use else 'No'}")
        if protocol.ibc_approval:
            lines.append(f"**IBC Approval:** {protocol.ibc_approval}")
        lines.append("")
        
        # Footer
        lines.append("---")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        
        content = "\n".join(lines)
        
        if output_path:
            output_path.write_text(content, encoding="utf-8")
        
        return content


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def export_to_pdf(
    protocol: Protocol,
    output_path: Optional[Path] = None,
    institution_name: str = "University Research Institution",
) -> bytes:
    """
    Export protocol to PDF.
    
    Args:
        protocol: Protocol to export
        output_path: Optional output file path
        institution_name: Institution name for header
        
    Returns:
        PDF bytes.
    """
    exporter = PDFExporter(institution_name=institution_name)
    return exporter.export(protocol, output_path)


def export_to_markdown(
    protocol: Protocol,
    output_path: Optional[Path] = None,
    institution_name: str = "University Research Institution",
) -> str:
    """
    Export protocol to Markdown.
    
    Args:
        protocol: Protocol to export
        output_path: Optional output file path
        institution_name: Institution name for header
        
    Returns:
        Markdown string.
    """
    exporter = MarkdownExporter(institution_name=institution_name)
    return exporter.export(protocol, output_path)


# Export
__all__ = [
    "PDFExporter",
    "MarkdownExporter",
    "export_to_pdf",
    "export_to_markdown",
]
