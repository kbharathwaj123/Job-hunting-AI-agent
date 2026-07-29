import os
import tempfile
import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

def generate_pdf_report(applications: list, output_path: str = "C:/Users/HP/Downloads/JobsApplied.pdf"):
    """
    Generates a 2-section A4 Landscape PDF report separating Domestic (India) and International applications.
    Displays detailed status reasons, compact 11-12px typography, Applied Via platform badges,
    and clickable Base64 proof screenshots that open inline in full resolution (without downloading).
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Job Application Executive Report</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
            
            @page {
                size: A4 landscape;
                margin: 8mm;
            }

            body {
                font-family: 'Plus Jakarta Sans', sans-serif;
                background-color: #f8fafc;
                color: #0f172a;
                margin: 0;
                padding: 10px;
                -webkit-print-color-adjust: exact;
            }
            
            .container {
                width: 100%;
                margin: 0 auto;
                background: #ffffff;
                padding: 20px;
                border-radius: 14px;
                box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
                border: 1px solid #cbd5e1;
                box-sizing: border-box;
            }
            
            .header-banner {
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                color: #ffffff;
                padding: 18px 22px;
                border-radius: 10px;
                margin-bottom: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header-banner h1 {
                font-family: 'Outfit', sans-serif;
                font-size: 22px;
                font-weight: 800;
                margin: 0;
                letter-spacing: -0.02em;
            }
            
            .header-banner p {
                color: #94a3b8;
                margin: 3px 0 0 0;
                font-size: 12px;
                font-weight: 500;
            }
            
            .date-badge {
                background: rgba(255, 255, 255, 0.12);
                padding: 6px 14px;
                border-radius: 99px;
                font-family: 'Outfit', sans-serif;
                font-weight: 600;
                font-size: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 12px;
                margin-bottom: 18px;
            }
            
            .stat-card {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 12px 14px;
            }
            
            .stat-card .label {
                font-size: 10.5px;
                font-weight: 700;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 3px;
            }
            
            .stat-card .value {
                font-family: 'Outfit', sans-serif;
                font-size: 22px;
                font-weight: 700;
                color: #1e293b;
            }
            
            .stat-card.applied-card { border-left: 4px solid #10b981; }
            .stat-card.staged-card { border-left: 4px solid #f59e0b; }
            .stat-card.skipped-card { border-left: 4px solid #ef4444; }
            .stat-card.already-card { border-left: 4px solid #8b5cf6; }

            .section-header {
                font-family: 'Outfit', sans-serif;
                font-size: 15px;
                font-weight: 700;
                color: #1e293b;
                padding: 8px 12px;
                background-color: #f1f5f9;
                border-left: 5px solid #2563eb;
                border-radius: 6px;
                margin-top: 18px;
                margin-bottom: 10px;
            }

            .section-header.international-header {
                border-left-color: #7c3aed;
                background-color: #f5f3ff;
            }
            
            .table-container {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 16px;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
                background: #ffffff;
                table-layout: fixed;
            }
            
            th {
                background-color: #f8fafc;
                color: #334155;
                font-family: 'Outfit', sans-serif;
                font-weight: 700;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                padding: 8px 10px;
                border-bottom: 2px solid #cbd5e1;
            }
            
            td {
                padding: 7px 9px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 11px;
                color: #334155;
                vertical-align: middle;
                word-wrap: break-word;
                line-height: 1.3;
            }
            
            tr:nth-child(even) { background-color: #f8fafc; }
            
            .badge {
                display: inline-block;
                padding: 3px 7px;
                border-radius: 5px;
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                white-space: nowrap;
            }
            
            .badge-applied { background-color: #dcfce7; color: #15803d; }
            .badge-staged { background-color: #fef3c7; color: #b91c1c; }
            .badge-skipped { background-color: #fee2e2; color: #b91c1c; }
            .badge-already { background-color: #f3e8ff; color: #6b21a8; border: 1px solid #d8b4fe; }
            .badge-error { background-color: #f1f5f9; color: #475569; }
            
            .reason-text {
                font-size: 9.5px;
                color: #64748b;
                display: block;
                margin-top: 2px;
                font-weight: 500;
            }

            .source-tag {
                display: inline-block;
                padding: 3px 6px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 700;
                white-space: nowrap;
            }
            
            .source-company { background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
            .source-linkedin { background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
            .source-naukri { background-color: #fff7ed; color: #c2410c; border: 1px solid #ffedd5; }
            .source-indeed { background-color: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; }

            .score-tag {
                font-family: 'Outfit', sans-serif;
                font-weight: 700;
                font-size: 11.5px;
            }
            .score-high { color: #16a34a; }
            .score-med { color: #d97706; }
            .score-low { color: #dc2626; }
            
            .email-text {
                font-family: monospace;
                color: #475569;
                font-size: 10px;
                word-break: break-all;
            }

            .proof-img {
                width: 85px;
                height: 50px;
                object-fit: cover;
                border-radius: 6px;
                border: 1px solid #cbd5e1;
                cursor: pointer;
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }
            .proof-img:hover {
                transform: scale(1.05);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .no-proof {
                font-size: 9.5px;
                color: #94a3b8;
                font-style: italic;
            }

            /* LIGHTBOX MODAL FOR FULL SCREEN VIEW WITHOUT DOWNLOADING */
            .lightbox-modal {
                display: none;
                position: fixed;
                z-index: 9999;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(15, 23, 42, 0.85);
                backdrop-filter: blur(4px);
                justify-content: center;
                align-items: center;
            }
            .lightbox-content {
                max-width: 90%;
                max-height: 90%;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                border: 2px solid #ffffff;
            }
            .close-btn {
                position: absolute;
                top: 20px;
                right: 30px;
                color: #ffffff;
                font-size: 32px;
                font-weight: bold;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-banner">
                <div>
                    <h1>JobsApplied Executive Report</h1>
                    <p>3-Month Rolling Window & Multi-Channel Application Log</p>
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
                <div class="stat-card already-card">
                    <div class="label">Already Applied (3-Mo)</div>
                    <div class="value">__ALREADY_COUNT__</div>
                </div>
                <div class="stat-card skipped-card">
                    <div class="label">Skipped / Low Rating</div>
                    <div class="value">__SKIPPED_COUNT__</div>
                </div>
            </div>
            
            <!-- SECTION 1: DOMESTIC APPLICATIONS -->
            <div class="section-header">🇮🇳 Section 1: Domestic Applications (India - Hyderabad, Pune, Bangalore, Kochi)</div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 18%;">Company & Title</th>
                            <th style="width: 15%;">Email</th>
                            <th style="width: 10%;">Salary</th>
                            <th style="width: 10%;">Work Type</th>
                            <th style="width: 8%;">ATS Match</th>
                            <th style="width: 11%;">Location</th>
                            <th style="width: 9%;">Applied Via</th>
                            <th style="width: 11%;">Status & Reason</th>
                            <th style="width: 8%;">Proof</th>
                        </tr>
                    </thead>
                    <tbody>
                        __DOMESTIC_ROWS__
                    </tbody>
                </table>
            </div>

            <!-- SECTION 2: INTERNATIONAL APPLICATIONS -->
            <div class="section-header international-header">🌐 Section 2: International Applications (US, UK, France, Germany, Japan, Dubai, China)</div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 18%;">Company & Title</th>
                            <th style="width: 15%;">Email</th>
                            <th style="width: 10%;">Salary</th>
                            <th style="width: 10%;">Work Type</th>
                            <th style="width: 8%;">ATS Match</th>
                            <th style="width: 11%;">Location</th>
                            <th style="width: 9%;">Applied Via</th>
                            <th style="width: 11%;">Status & Reason</th>
                            <th style="width: 8%;">Proof</th>
                        </tr>
                    </thead>
                    <tbody>
                        __INTL_ROWS__
                    </tbody>
                </table>
            </div>
        </div>

        <!-- LIGHTBOX OVERLAY DIALOG -->
        <div id="imageModal" class="lightbox-modal" onclick="closeModal()">
            <span class="close-btn" onclick="closeModal()">&times;</span>
            <img class="lightbox-content" id="imgFull">
        </div>

        <script>
            function openModal(src) {
                document.getElementById("imgFull").src = src;
                document.getElementById("imageModal").style.display = "flex";
            }
            function closeModal() {
                document.getElementById("imageModal").style.display = "none";
            }
        </script>
    </body>
    </html>
    """
    
    intl_keywords = ["united states", "us", "uk", "london", "united kingdom", "paris", "france", "germany", "berlin", "munich", "japan", "tokyo", "dubai", "uae", "china", "shanghai", "beijing"]
    
    domestic_apps = []
    intl_apps = []
    
    for app in applications:
        loc_str = str(app.get("location", "")).lower()
        title_str = str(app.get("title", "")).lower()
        if any(kw in loc_str or kw in title_str for kw in intl_keywords):
            intl_apps.append(app)
        else:
            domestic_apps.append(app)

    total_jobs = len(applications)
    applied_count = sum(1 for app in applications if app.get('status') in ('applied', 'submitted'))
    already_count = sum(1 for app in applications if app.get('status') == 'already_applied')
    skipped_count = sum(1 for app in applications if app.get('status') in ('skipped_low_rating', 'suspicious', 'skipped', 'low_ats_score'))

    def build_rows(app_list):
        if not app_list:
            return '<tr><td colspan="9" style="text-align:center; color:#94a3b8; font-style:italic; padding:12px;">No applications recorded in this section yet.</td></tr>'
            
        rows_html = []
        for app in app_list:
            status = app.get('status', 'unknown').lower()
            reason = app.get('status_reason') or app.get('reason') or ''
            
            if status in ('applied', 'submitted'):
                badge_class = 'badge-applied'
                status_text = 'Applied'
            elif status == 'already_applied':
                badge_class = 'badge-already'
                status_text = 'Already Applied'
                reason = 'Applied within last 3 months'
            elif status == 'staged':
                badge_class = 'badge-staged'
                status_text = 'Review Req'
            elif status == 'skipped_low_rating':
                badge_class = 'badge-skipped'
                status_text = 'Low Rating'
            elif status == 'low_ats_score':
                badge_class = 'badge-skipped'
                status_text = 'Low ATS Match'
            elif status == 'suspicious':
                badge_class = 'badge-skipped'
                status_text = 'Suspicious'
            else:
                badge_class = 'badge-error'
                status_text = status.upper()
                
            reason_markup = f'<span class="reason-text">{reason[:45]}</span>' if reason else ''

            source_raw = str(app.get('source', 'company_portal')).lower()
            if 'linkedin' in source_raw:
                source_class = 'source-linkedin'
                source_label = 'LinkedIn'
            elif 'naukri' in source_raw:
                source_class = 'source-naukri'
                source_label = 'Naukri'
            elif 'indeed' in source_raw:
                source_class = 'source-indeed'
                source_label = 'Indeed'
            else:
                source_class = 'source-company'
                source_label = 'Company Portal'
                
            score = app.get('ats_score', 0)
            score_class = 'score-high' if score >= 80 else ('score-med' if score >= 55 else 'score-low')
                
            salary = app.get('salary') or 'Not Specified'
            wfh = app.get('wfh') or 'On-site / Hybrid / Remote'
            location = app.get('location') or 'Not Specified'
            email = app.get('company_email') or 'Not Listed'
            
            shot_path = app.get('screenshot') or app.get('screenshot_path') or ''
            if shot_path and os.path.exists(shot_path):
                try:
                    import base64
                    with open(shot_path, "rb") as img_f:
                        b64_data = base64.b64encode(img_f.read()).decode('utf-8')
                    proof_html = f'<img src="data:image/png;base64,{b64_data}" class="proof-img" onclick="openModal(this.src)" title="Click to view full screenshot (No Download)" alt="Proof"/>'
                except Exception:
                    proof_html = '<span class="no-proof">Proof Saved</span>'
            else:
                proof_html = '<span class="no-proof">Log Verified</span>'
            
            row = f"""
            <tr>
                <td><strong>{app.get('company', 'Company')}</strong><br><span style="font-size:10px;color:#64748b;font-weight:500;">{app.get('title', 'Role')}</span></td>
                <td class="email-text">{email}</td>
                <td>{salary}</td>
                <td>{wfh}</td>
                <td class="score-tag {score_class}">{score}%</td>
                <td>{location}</td>
                <td><span class="source-tag {source_class}">{source_label}</span></td>
                <td><span class="badge {badge_class}">{status_text}</span>{reason_markup}</td>
                <td>{proof_html}</td>
            </tr>
            """
            rows_html.append(row)
        return "\n".join(rows_html)

    domestic_rows_html = build_rows(domestic_apps)
    intl_rows_html = build_rows(intl_apps)

    today_str = datetime.date.today().strftime("%B %d, %Y")
    
    final_html = html_content.replace('__TOTAL_JOBS__', str(total_jobs))\
                             .replace('__APPLIED_COUNT__', str(applied_count))\
                             .replace('__ALREADY_COUNT__', str(already_count))\
                             .replace('__SKIPPED_COUNT__', str(skipped_count))\
                             .replace('__DATE__', today_str)\
                             .replace('__DOMESTIC_ROWS__', domestic_rows_html)\
                             .replace('__INTL_ROWS__', intl_rows_html)
    
    temp_dir = Path(tempfile.gettempdir())
    temp_html_path = temp_dir / "report_2sections.html"
    temp_html_path.write_text(final_html, encoding='utf-8')
    
    print(f"Generating Executive 2-Section PDF report (A4 Landscape) to: {output_path}")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(temp_html_path.as_uri())
        page.wait_for_timeout(1000)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        page.pdf(
            path=output_path,
            format="A4",
            landscape=True,
            margin={"top": "8mm", "bottom": "8mm", "left": "8mm", "right": "8mm"},
            print_background=True
        )
        browser.close()
        
    try:
        os.remove(temp_html_path)
    except OSError:
        pass
    print("PDF report generated successfully.")
