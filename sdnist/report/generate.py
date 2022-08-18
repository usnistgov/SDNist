import sys
import urllib.request
from pathlib import Path
from typing import Dict
from html.parser import HTMLParser
import codecs
import webbrowser

# from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
# from PyQt5.QtCore import QMarginsF, QSizeF
# from PyQt5.QtGui import QPageSize, QPageLayout, QTextDocument
# from PyQt5.QtPrintSupport import QPrinter
# from PyQt5.QtWidgets import QApplication
from jinja2 import Environment, FileSystemLoader

from sdnist.report import FILE_DIR

# app = QtWidgets.QApplication(sys.argv)
#
# page = QtWebEngineWidgets.QWebEnginePage()


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
#     file = codecs.open(str(html), "r", "utf-8")
#     data = file.read()
#     print(data)
#     # f = HTMLFilter()
#     # f.feed(data)
#     # html = f.text
#     print(data)
#     document.setHtml(data)
#
#     printer = QPrinter()
#     printer.setResolution(140)
#     printer.setPageSize(QPrinter.Letter)
#     printer.setOutputFormat(QPrinter.PdfFormat)
#     printer.setOutputFileName("test.pdf")
#     # printer.setPageMargins(12, 16, 12, 20, QPrinter.Millimeter)
#     document.setPageSize(QSizeF(printer.pageRect().size()))
#     print(document.pageSize(), printer.resolution(), printer.pageRect())
#
#     document.print_(printer)

# function taken from:
# https://stackoverflow.com/questions/63382399/how-to-convert-a-local-html-file-to-pdf-using-pyqt5
# def html_to_pdf(html: Path, pdf: Path):
#     html = str(html)
#     pdf = str(pdf)
#
#     def handle_print_finished(filename, status):
#         print("finished", filename)
#         app.quit()
#
#     def handle_load_finished(status):
#         if status:
#
#             q_layout = QPageLayout(QPageSize(QPageSize.A10),
#                                    QPageLayout.Orientation.Portrait,
#                                    QMarginsF(0, 10, 0, 10))
#             page.printToPdf(pdf, pageLayout=q_layout)
#         else:
#             print("Failed")
#             app.quit()
#
#     page.pdfPrintingFinished.connect(handle_print_finished)
#     page.loadFinished.connect(handle_load_finished)
#     page.load(QtCore.QUrl.fromLocalFile(html))
#     app.exec_()




def generate(report_data: Dict[str, any],
             output_directory_path: Path):
    out_dir = output_directory_path
    data = report_data

    env = Environment(loader=FileSystemLoader(Path(FILE_DIR, 'resources/templates')))
    env.globals["enumerate"] = enumerate

    main_template = env.get_template('main.jinja2')

    out = main_template.render(data=data)

    out_path = Path(out_dir, 'report.html')
    out_pdf_path = Path(out_dir, 'report.pdf')

    with open(out_path, 'w') as f:
        f.write(out)

    webbrowser.open(f"file://{out_path}", new=True)
    # html_to_pdf(out_path, out_pdf_path)


if __name__ == "__main__":
    h_p = Path(FILE_DIR, '../../reports/TX_ACS_EXCERPT_2019_08-02-2022T15.14.12/report.html')
    p_p = Path(FILE_DIR, '../../reports/TX_ACS_EXCERPT_2019_08-02-2022T15.14.12/report.pdf')
    p_o = Path(FILE_DIR, '../../reports/TX_ACS_EXCERPT_2019_08-02-2022T15.14.12/report0.pdf')

    html_to_pdf_2(h_p, p_p)




