import sys
from pathlib import Path
from typing import Dict

import webbrowser

from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
from jinja2 import Environment, FileSystemLoader

from sdnist.report import FILE_DIR


# function taken from:
# https://stackoverflow.com/questions/63382399/how-to-convert-a-local-html-file-to-pdf-using-pyqt5
def html_to_pdf(html: Path, pdf: Path):
    html = str(html)
    pdf = str(pdf)
    app = QtWidgets.QApplication(sys.argv)

    page = QtWebEngineWidgets.QWebEnginePage()

    def handle_print_finished(filename, status):
        print("finished", filename, status)
        QtWidgets.QApplication.quit()

    def handle_load_finished(status):
        if status:
            page.printToPdf(pdf)
        else:
            print("Failed")
            QtWidgets.QApplication.quit()

    page.pdfPrintingFinished.connect(handle_print_finished)
    page.loadFinished.connect(handle_load_finished)
    page.load(QtCore.QUrl.fromLocalFile(html))
    app.exec_()


def generate(report_data: Dict[str, any],
             output_directory_path: Path):
    out_dir = output_directory_path
    data = report_data
    print(data)
    env = Environment(loader=FileSystemLoader(Path(FILE_DIR, 'resources/templates')))

    main_template = env.get_template('main.jinja2')

    out = main_template.render(data=data)

    out_path = Path(out_dir, 'report.html')
    out_pdf_path = Path(out_dir, 'report.pdf')

    with open(out_path, 'w') as f:
        f.write(out)

    webbrowser.open(f"file://{out_path}", new=True)
    html_to_pdf(out_path, out_pdf_path)






