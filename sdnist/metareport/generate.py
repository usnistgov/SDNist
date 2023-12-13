import sys
import urllib.request
from pathlib import Path
from typing import Dict
from html.parser import HTMLParser
import codecs
import webbrowser

from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
from PyQt5.QtCore import QMarginsF, QSizeF
from PyQt5.QtGui import QPageSize, QPageLayout, QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QApplication
from jinja2 import Environment, FileSystemLoader

app = QtWidgets.QApplication(sys.argv)

page = QtWebEngineWidgets.QWebEnginePage()


# def html_to_pdf_2(html: Path, pdf: Path):
#     a = QApplication([])
#     document = QTextDocument()
#
#     class HTMLFilter(HTMLParser):
#         text = ""
#
#         def handle_data(self, data):
#             self.text += data
#
#     file = codecs.open(str(html), "r")
#     data = file.read()
#     # print(data)
#     # # f = HTMLFilter()
#     # # f.feed(data)
#     # # html = f.text
#     # print(data)
#     document.setHtml(data)
#
#     printer = QPrinter()
#     printer.setResolution(140)
#     printer.setPageSize(QPrinter.Letter)
#     printer.setOutputFormat(QPrinter.PdfFormat)
#     printer.setOutputFileName(str(pdf))
#     # printer.setPageMargins(12, 16, 12, 20, QPrinter.Millimeter)
#     document.setPageSize(QSizeF(printer.pageRect().size()))
#     # print(document.pageSize(), printer.resolution(), printer.pageRect())
#
#     document.print_(printer)

# function taken from:
# https://stackoverflow.com/questions/63382399/how-to-convert-a-local-html-file-to-pdf-using-pyqt5
def html_to_pdf(html: Path, pdf: Path):
    s_html = str(html)
    s_pdf = str(pdf)

    def handle_print_finished(filename, status):
        print("finished", filename)
        app.quit()

    def handle_load_finished(status):
        if status:

            q_layout = QPageLayout(QPageSize(QPageSize.A4),
                                   QPageLayout.Orientation.Portrait,
                                   QMarginsF(10, 40, 10, 40))
            page.printToPdf(s_pdf, pageLayout=q_layout)
        else:
            print("Failed")
            app.quit()

    page.pdfPrintingFinished.connect(handle_print_finished)
    page.loadFinished.connect(handle_load_finished)
    page.load(QtCore.QUrl.fromLocalFile(s_html))
    app.exec_()


def debug(text):
  print(text)
  return ''

def generate(report_data: Dict[str, any],
             output_directory_path: Path,
             open_in_browser: bool = False):
    out_dir = output_directory_path
    data = report_data
    FILE_DIR = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(Path(FILE_DIR, 'resources')))
    env.globals["enumerate"] = enumerate
    env.filters['debug'] = debug
    main_template = env.get_template('main.jinja2')
    pdf_template = env.get_template('pdf.jinja2')

    out_main = main_template.render(data=data)
    out_temp = pdf_template.render(data=data)

    out_path_main = Path(out_dir, 'report.html')
    out_path_temp = Path(out_dir, 'report_temp.html')
    out_pdf_path = Path(out_dir, 'report.pdf')

    with open(out_path_main, 'w') as f:
        f.write(out_main)
    with open(out_path_temp, 'w') as f:
        f.write(out_temp)

    if open_in_browser:
        webbrowser.open(f"file://{out_path_main}", new=True)
    html_to_pdf(out_path_temp, out_pdf_path)

    if out_path_temp.exists():
        out_path_temp.unlink()





