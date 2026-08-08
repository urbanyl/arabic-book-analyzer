from pathlib import Path
from datetime import datetime
from typing import List
from ..models.book import Citation


class Exporter:
    def __init__(self, export_dir: Path = None):
        from config import EXPORT_DIR
        self.export_dir = export_dir or EXPORT_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_txt(self, citations: List[Citation], query: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resultats_{timestamp}.txt"
        filepath = self.export_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"نتائج البحث عن: {query}\n")
            f.write(f"تاريخ البحث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"عدد النتائج: {len(citations)}\n")
            f.write("=" * 60 + "\n\n")

            for i, cit in enumerate(citations, 1):
                f.write(f"--- نتيجة {i} ---\n")
                f.write(f"النص: {cit.text}\n")
                f.write(f"الكتاب: {cit.book_title}\n")
                f.write(f"المؤلف: {cit.author}\n")
                f.write(f"الجزء: {cit.tome}\n")
                f.write(f"الصفحة: {cit.page}\n")
                f.write(f"المرجع: {cit.reference}\n")
                f.write("\n" + "=" * 60 + "\n\n")

        return filepath

    def export_html(self, citations: List[Citation], query: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rapport_{timestamp}.html"
        filepath = self.export_dir / filename

        html = self._generate_html_report(citations, query, timestamp)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        return filepath

    def _generate_html_report(self, citations: List[Citation], query: str, timestamp: str) -> str:
        rows = ""
        for i, cit in enumerate(citations, 1):
            rows += f"""
            <tr>
                <td>{i}</td>
                <td class="citation-text" dir="rtl">{cit.text}</td>
                <td>{cit.book_title}</td>
                <td>{cit.author}</td>
                <td>{cit.tome}</td>
                <td>{cit.page}</td>
                <td>{cit.reference}</td>
            </tr>"""

        empty_row = ""
        if not citations:
            empty_row = """
            <tr>
                <td colspan="7" class="empty-result">لا يوجد</td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تقرير البحث - {query}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Noto+Naskh+Arabic:wght@400;700&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Noto Naskh Arabic', 'Amiri', serif;
            background: #f5f0e8;
            color: #2c1810;
            line-height: 1.8;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #1a5c3a, #2d8f5e);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}

        .header .meta {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 20px;
            background: #faf7f2;
            border-bottom: 2px solid #e8e0d0;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #1a5c3a;
        }}

        .stat-label {{
            color: #666;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 0;
        }}

        th {{
            background: #1a5c3a;
            color: white;
            padding: 15px 10px;
            font-size: 1.05em;
            font-weight: bold;
        }}

        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #e8e0d0;
            vertical-align: top;
        }}

        tr:nth-child(even) {{
            background: #faf7f2;
        }}

        tr:hover {{
            background: #f0ebe0;
        }}

        .citation-text {{
            font-size: 1.15em;
            line-height: 2;
            font-family: 'Amiri', serif;
            max-width: 400px;
        }}

        .empty-result {{
            text-align: center;
            padding: 40px;
            font-size: 1.5em;
            color: #888;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #888;
            font-size: 0.9em;
            border-top: 1px solid #e8e0d0;
        }}

        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; }}
            .header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>تقرير البحث</h1>
            <div class="meta">
                <p>موضوع البحث: <strong>{query}</strong></p>
                <p>تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(citations)}</div>
                <div class="stat-label">نتيجة</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(set(c.book_title for c in citations))}</div>
                <div class="stat-label">كتاب</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>الرقم</th>
                    <th>الاقتباس</th>
                    <th>الكتاب</th>
                    <th>المؤلف</th>
                    <th>الجزء</th>
                    <th>الصفحة</th>
                    <th>المرجع</th>
                </tr>
            </thead>
            <tbody>
                {rows if citations else empty_row}
            </tbody>
        </table>

        <div class="footer">
            <p>تم إنشاء هذا التقرير بواسطة برنامج تحليل الكتب العربية بالذكاء الاصطناعي</p>
        </div>
    </div>
</body>
</html>"""
