import os
import tempfile
import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

def generate_pdf_report(applications: list, output_path: str = "C:/Users/HP/Downloads/JobsApplied.pdf"):
    """
    Generates an exceptionally beautiful, professionally-styled PDF report
    listing job applications and statuses.
    """
    # Premium HTML template with CSS grid, cards, and custom fonts
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Job Application Status Report</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
            
            body {
                font-family: 'Plus Jakarta Sans', sans-serif;
                background-color: #f8fafc;
                color: #0f172a;
                margin: 0;
                padding: 30px;
                -webkit-print-color-adjust: exact;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: #ffffff;
                padding: 40px;
                border-radius: 24px;
                box-shadow: 0 10px 40px rgba(15, 23, 42, 0.04);
                border: 1px solid #e2e8f0;
            }
            
            .header-banner {
                background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%);
                color: #ffffff;
                padding: 35px 40px;
                border-radius: 20px;
                margin-bottom: 35px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 8px 30px rgba(79, 70, 229, 0.15);
            }
            
            .header-banner h1 {
                font-family: 'Outfit', sans-serif;
                font-size: 32px;
                font-weight: 800;
                margin: 0;
                letter-spacing: -0.03em;
            }
            
            .header-banner p {
                color: #cbd5e1;
                margin: 6px 0 0 0;
                font-size: 15px;
                font-weight: 500;
            }
            
            .date-badge {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(8px);
                padding: 10px 20px;
                border-radius: 99px;
                font-family: 'Outfit', sans-serif;
                font-weight: 600;
                font-size: 14px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 35px;
            }
            
            .stat-card {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                padding: 20px;
                text-align: left;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);
                transition: transform 0.2s;
            }
            
            .stat-card .label {
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.07em;
                margin-bottom: 6px;
            }
            
            .stat-card .value {
                font-family: 'Outfit', sans-serif;
                font-size: 30px;
                font-weight: 700;
                color: #1e293b;
            }
            
            .stat-card.applied-card {
                border-left: 5px solid #10b981;
            }
            .stat-card.skipped-card {
                border-left: 5px solid #ef4444;
            }
            .stat-card.staged-card {
                border-left: 5px solid #f59e0b;
            }
            
            .table-container {
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
                background: #ffffff;
            }
            
            th {
                background-color: #f8fafc;
                color: #475569;
                font-family: 'Outfit', sans-serif;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                padding: 18px 20px;
                border-bottom: 2px solid #e2e8f0;
            }
            
            td {
                padding: 18px 20px;
                border-bottom: 1px solid #f1f5f9;
                font-size: 13.5px;
                color: #334155;
                vertical-align: middle;
            }
            
            tr:last-child td {
                border-bottom: none;
            }
            
            tr:nth-child(even) {
                background-color: #f8fafc;
            }
            
            .badge {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 99px;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            .badge-applied {
                background-color: #dcfce7;
                color: #15803d;
            }
            
            .badge-staged {
                background-color: #fef3c7;
                color: #d97706;
            }
            
            .badge-skipped {
                background-color: #fee2e2;
                color: #b91c1c;
            }
            
            .badge-error {
                background-color: #f1f5f9;
                color: #475569;
            }
            
            .score-tag {
                font-family: 'Outfit', sans-serif;
                font-weight: 700;
                font-size: 14px;
            }
            
            .score-high {
                color: #16a34a;
            }
            
            .score-med {
                color: #d97706;
            }
            
            .score-low {
                color: #dc2626;
            }
            
            .email-text {
                font-family: monospace;
                color: #64748b;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-banner">
                <div>
                    <h1>JobsApplied Report</h1>
                    <p>Automated Job Search & Application Log</p>
                </div>
                <div class="date-badge">__DATE__</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">Total Processed</div>
                    <div class="value">__TOTAL_JOBS__</div>
                </div>
                <div class="stat-card applied-card">
                    <div class="label">Applied</div>
                    <div class="value">__APPLIED_COUNT__</div>
                </div>
                <div class="stat-card staged-card">
                    <div class="label">Review Required / Staged</div>
                    <div class="value">__STAGED_COUNT__</div>
                </div>
                <div class="stat-card skipped-card">
                    <div class="label">Skipped (Low Rating)</div>
                    <div class="value">__SKIPPED_COUNT__</div>
                </div>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Company Name</th>
                            <th>Company Email</th>
                            <th>Offering Salary</th>
                            <th>WFH/Hybrid</th>
                            <th>ATS Match %</th>
                            <th>Location</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        __TABLE_ROWS__
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Calculate counts
    total_jobs = len(applications)
    applied_count = sum(1 for app in applications if app.get('status') == 'applied' or app.get('status') == 'submitted')
    staged_count = sum(1 for app in applications if app.get('status') == 'staged')
    skipped_count = sum(1 for app in applications if app.get('status') == 'skipped_low_rating' or app.get('status') == 'suspicious')
    
    # Render table rows
    rows_html = []
    for app in applications:
        # Style status badge
        status = app.get('status', 'unknown').lower()
        if status in ('applied', 'submitted'):
            badge_class = 'badge-applied'
            status_text = 'Applied'
        elif status == 'staged':
            badge_class = 'badge-staged'
            status_text = 'Review Req'
        elif status in ('skipped_low_rating', 'suspicious'):
            badge_class = 'badge-skipped'
            status_text = 'Low Rating'
        elif status == 'skipped':
            badge_class = 'badge-error'
            status_text = 'Skipped'
        else:
            badge_class = 'badge-error'
            status_text = status.upper()
            
        # Style ATS score
        score = app.get('ats_score', 0)
        if score >= 80:
            score_class = 'score-high'
        elif score >= 60:
            score_class = 'score-med'
        else:
            score_class = 'score-low'
            
        salary = app.get('salary') or 'Not Specified'
        wfh = app.get('wfh') or 'Remote/Hybrid'
        location = app.get('location') or 'Not Specified'
        email = app.get('company_email') or 'Not Listed'
        
        row = f"""
        <tr>
            <td><strong>{app.get('company')}</strong><br><span style="font-size:11px;color:#64748b;font-weight:500;">{app.get('title')}</span></td>
            <td class="email-text">{email}</td>
            <td>{salary}</td>
            <td>{wfh}</td>
            <td class="score-tag {score_class}">{score}%</td>
            <td>{location}</td>
            <td><span class="badge {badge_class}">{status_text}</span></td>
        </tr>
        """
        rows_html.append(row)
        
    today_str = datetime.date.today().strftime("%B %d, %Y")
    
    final_html = html_content.replace('__TOTAL_JOBS__', str(total_jobs))\
                             .replace('__APPLIED_COUNT__', str(applied_count))\
                             .replace('__STAGED_COUNT__', str(staged_count))\
                             .replace('__SKIPPED_COUNT__', str(skipped_count))\
                             .replace('__DATE__', today_str)\
                             .replace('__TABLE_ROWS__', "\n".join(rows_html))
    
    # Write to a temporary file
    temp_dir = Path(tempfile.gettempdir())
    temp_html_path = temp_dir / "report.html"
    temp_html_path.write_text(final_html, encoding='utf-8')
    
    # Render to PDF using Playwright
    print(f"Generating PDF report to: {output_path}")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(temp_html_path.as_uri())
        page.wait_for_timeout(1000) # wait for fonts/styles
        
        # Output PDF
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        page.pdf(
            path=output_path,
            format="A4",
            margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"},
            print_background=True
        )
        browser.close()
        
    # Clean up temp file
    try:
        os.remove(temp_html_path)
    except OSError:
        pass
    print("PDF report generated successfully.")
