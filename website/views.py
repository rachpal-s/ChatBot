from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note
from . import db
import json
import google.generativeai as genai
GOOGLE_API_KEY= "AIzaSyBAk95kSqBeP81IqAObnwrAWMYDt3omMYQ"
genai.configure(api_key=GOOGLE_API_KEY)
views = Blueprint('views', __name__)
model = genai.GenerativeModel('gemini-pro')
message_history = []

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')#Gets the note from the HTML 

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            result = model.generate_content(note)
            processed_result=result.text
            new_note = Note(data="Query: " + note, user_id=current_user.id)  #providing the schema for the note 
            db.session.add(new_note) #adding the note to the database 
            db.session.commit()

            # Answer for the query
            answer = Note(data=processed_result, user_id=current_user.id)
            db.session.add(answer) #adding the answer to the database 
            db.session.commit()

            flash('Query answered!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})
