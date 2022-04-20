from pathlib import Path
from typing import Dict

import webbrowser
from xhtml2pdf import pisa
from jinja2 import Template, Environment, FileSystemLoader

from sdnist.report import FILE_DIR, REPORTS_DIR
from sdnist.report.report_data import ReportData


def generate(report_data: Dict[str, any]):
    data = report_data
    print(data)
    env = Environment(loader=FileSystemLoader(Path(FILE_DIR, 'resources/templates')))

    main_template = env.get_template('main.jinja2')

    out = main_template.render(data=data)

    out_path = Path(REPORTS_DIR, 'main.html')
    out_pdf_path = Path(REPORTS_DIR, 'main.pdf')
    with open(out_path, 'w') as f:
        f.write(out)

    webbrowser.open(f"file://{out_path}", new=True)

    res_file = open(out_pdf_path, "w+b")
    html_file = out_path.open('r')
    pisa_status = pisa.CreatePDF(html_file, dest=res_file)

    res_file.close()






