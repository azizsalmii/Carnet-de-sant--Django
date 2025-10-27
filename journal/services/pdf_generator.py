import os
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import datetime

class PDFGenerator:
    """Générateur de rapports PDF pour les données santé"""
    
    def generate_health_report_pdf(self, report, health_data_list):
        """Génère un PDF détaillé du rapport santé"""
        try:
            # Créer le buffer pour le PDF
            buffer = BytesIO()
            
            # Créer le document PDF
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Conteneur pour les éléments du PDF
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                textColor=colors.HexColor('#2E86AB')
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=12,
                textColor=colors.HexColor('#2E86AB')
            )
            
            # Titre du rapport
            title = Paragraph(f"RAPPORT SANTÉ - {report.month.strftime('%B %Y').upper()}", title_style)
            elements.append(title)
            
            # Informations générales
            elements.append(Paragraph("Informations Générales", heading_style))
            info_data = [
                ['Patient:', report.user.get_full_name() or report.user.username],
                ['Mois analysé:', report.month.strftime('%B %Y')],
                ['Date de génération:', report.generated_at.strftime('%d/%m/%Y à %H:%M')],
                ['Score santé:', f"{report.health_score or 'N/A'}/100"]
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9FA')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 20))
            
            # Résumé du mois
            if report.report_content.get('summary'):
                elements.append(Paragraph("Résumé du Mois", heading_style))
                summary = report.report_content['summary']
                summary_data = [
                    ['Jours suivis:', str(summary.get('total_days_tracked', 0))],
                    ['Score santé:', f"{summary.get('health_score', 0)}/100"],
                    ['Tendance générale:', summary.get('overall_trend', 'N/A')],
                ]
                
                summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
                summary_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(summary_table)
                elements.append(Spacer(1, 20))
            
            # Analyse du sommeil
            if report.report_content.get('sleep_analysis'):
                elements.append(Paragraph("Analyse du Sommeil", heading_style))
                sleep = report.report_content['sleep_analysis']
                if not sleep.get('message'):
                    sleep_data = [
                        ['Durée moyenne:', f"{sleep.get('average_duration', 0)} heures"],
                        ['Qualité moyenne:', f"{sleep.get('average_quality', 0)}/5"],
                        ['Consistance:', sleep.get('sleep_consistency', 'N/A')],
                    ]
                    
                    sleep_table = Table(sleep_data, colWidths=[2*inch, 3*inch])
                    sleep_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ]))
                    elements.append(sleep_table)
                else:
                    elements.append(Paragraph(sleep['message'], styles['Normal']))
                elements.append(Spacer(1, 20))
            
            # Analyse de l'activité
            if report.report_content.get('activity_analysis'):
                elements.append(Paragraph("Analyse de l'Activité", heading_style))
                activity = report.report_content['activity_analysis']
                if not activity.get('message'):
                    activity_data = [
                        ['Pas moyens par jour:', f"{activity.get('average_steps', 0):,}"],
                        ['Exercice moyen:', f"{activity.get('average_exercise_minutes', 0)} minutes"],
                        ['Niveau d\'activité:', activity.get('activity_level', 'N/A')],
                    ]
                    
                    activity_table = Table(activity_data, colWidths=[2*inch, 3*inch])
                    activity_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ]))
                    elements.append(activity_table)
                else:
                    elements.append(Paragraph(activity['message'], styles['Normal']))
                elements.append(Spacer(1, 20))
            
            # Recommandations
            if report.recommendations:
                elements.append(Paragraph("Recommandations", heading_style))
                for i, recommendation in enumerate(report.recommendations, 1):
                    elements.append(Paragraph(f"{i}. {recommendation}", styles['Normal']))
                elements.append(Spacer(1, 20))
            
            # Facteurs de risque
            if report.risk_factors:
                elements.append(Paragraph("Facteurs de Risque Identifiés", heading_style))
                for risk in report.risk_factors:
                    elements.append(Paragraph(f"• {risk}", styles['Normal']))
                elements.append(Spacer(1, 20))
            
            # Statistiques détaillées
            if report.report_content.get('statistics'):
                elements.append(Paragraph("Statistiques Détaillées", heading_style))
                stats = report.report_content['statistics']
                stats_data = [
                    ['Jours avec données:', str(stats.get('days_with_data', 0))],
                    ['Taux d\'observance:', f"{stats.get('medication_adherence_rate', 0)}%"],
                    ['Jours sans symptômes:', str(stats.get('symptom_free_days', 0))],
                ]
                
                stats_table = Table(stats_data, colWidths=[2*inch, 3*inch])
                stats_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                elements.append(stats_table)
            
            # Générer le PDF
            doc.build(elements)
            
            # Récupérer le PDF du buffer
            pdf = buffer.getvalue()
            buffer.close()
            
            return pdf
            
        except Exception as e:
            print(f"Erreur génération PDF: {e}")
            # PDF d'erreur simple
            return self._generate_error_pdf(str(e))
    
    def _generate_error_pdf(self, error_message):
        """Génère un PDF d'erreur simple"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.drawString(100, 750, "Erreur lors de la génération du rapport")
        p.drawString(100, 730, f"Détails: {error_message}")
        p.drawString(100, 710, "Veuillez contacter l'administrateur.")
        p.showPage()
        p.save()
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def generate_simple_pdf(self, report):
        """Version simplifiée pour les tests"""
        try:
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            
            # En-tête
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, 800, f"Rapport Santé - {report.month.strftime('%B %Y')}")
            
            # Informations de base
            p.setFont("Helvetica", 12)
            p.drawString(100, 770, f"Patient: {report.user.get_full_name() or report.user.username}")
            p.drawString(100, 750, f"Score santé: {report.health_score or 'N/A'}/100")
            p.drawString(100, 730, f"Généré le: {report.generated_at.strftime('%d/%m/%Y')}")
            
            # Recommandations
            if report.recommendations:
                p.drawString(100, 700, "Recommandations:")
                y_position = 680
                for rec in report.recommendations[:5]:  # Limite à 5 recommandations
                    p.drawString(120, y_position, f"• {rec}")
                    y_position -= 20
                    if y_position < 100:  # Nouvelle page si nécessaire
                        p.showPage()
                        y_position = 750
            
            p.showPage()
            p.save()
            
            pdf = buffer.getvalue()
            buffer.close()
            return pdf
            
        except Exception as e:
            return self._generate_error_pdf(str(e))