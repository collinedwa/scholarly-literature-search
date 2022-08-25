import study_search_ver2 as s
import os
from flask import Flask, request, redirect, session, send_from_directory

app = Flask(__name__, static_folder='static')
app.secret_key = 'super_secret_key'

@app.route('/', methods = ['GET', 'POST'])
def index():
    session['done'] = False
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        results_num = int(request.form.get('results_num'))
        session['keyword'] = keyword
        session['results_num'] = results_num
        study = s.StudySearch(keyword, results_num, False)
        results = study.search_to_df()
        if not results:
            return redirect('/error')
        else:
            df = results.to_html()
            session['filename'] = study.study_exporter(results)
            session['done'] = True
            return f'''<h1>Search Results</h1>
            {df}
            <p><a href="/download"><button class=grey style="height:50px;width:100px">Download</button></a></p>
            <p><a href="../"><button class=grey style="height:50px;width:100px">Back</button></a></p>
            '''
    return '''<h1>Scholarly Literature Search</h1>
    <form method="POST">
               <div><label>Keyword: <input type="text" name="keyword"></label></div>
               <div><label>Number of Results: <input type="number" name="results_num" min="1"></label></div>
               <input type="submit" value="Submit">
           </form>
    '''
@app.route('/download')
def download():
    if not session['done']:
        return redirect('/')
    filename = session['filename']
    return send_from_directory(app.static_folder, f'{filename}.csv')

@app.route('/error')
def error():
    return '''<h1>No studies found!</h1>
    <p>Please alter your search terms.</p>
    <p><a href="../"><button class=grey style="height:50px;width:100px">Back</button></a></p>
    '''
