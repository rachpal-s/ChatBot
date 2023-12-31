from website import create_app
from flask import render_template 

app = create_app()

@app.errorhandler(Exception)
def handle_exception(error):
    return render_template('error.html', error=error), 500


if __name__ == '__main__':
    app.run(debug=True, host="localhost")
