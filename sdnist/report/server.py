from pathlib import Path
from flask import Flask, render_template
from jinja2 import Template, Environment, FileSystemLoader

FILE_DIR = Path(__file__).parent

app = Flask(__name__,
            template_folder=str(Path(FILE_DIR, 'resources', 'templates')))
app.jinja_env.auto_reload = True
app.config["TEMPLATES_AUTO_RELOAD"] = True


def setup():
    # env = Environment(loader=FileSystemLoader(Path(FILE_DIR, 'resources/templates')))
    #
    # main_template = env.get_template('main.jinja2')
    navigation = [{"item": f'link - {i}', "caption": f'caption - {i}'}
                  for i in range(5)]
    a_variable = "hello world"
    data = {"navigation": navigation, "a_variable": a_variable}

    @app.route('/')
    def index():
        print('home')
        return render_template('main.jinja2', **data)


if __name__ == '__main__':
    setup()
    app.run(host='0.0.0.0', port=5000, debug=True)
