from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Test, Question
import json

app = flask(__name__)
con_str= "mysql://root:cset155@localhost/" 

@app.route('/create_test', methods=['GET', 'POST'])
@login_required
def create_test():
    if current_user.role != "teacher":
        flash("Only teachers can create tests!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        questions = request.form.getlist('questions')
        question_types = request.form.getlist('question_types')
        options = request.form.getlist('options')

        new_test = Test(title=title, teacher_id=current_user.id)
        db.session.add(new_test)
        db.session.commit()

        for i in range(len(questions)):
            question_text = questions[i]
            q_type = question_types[i]
            q_options = json.dumps(options[i].split(',')) if q_type == "mcq" else None

            new_question = Question(test_id=new_test.id, text=question_text, question_type=q_type, options=q_options)
            db.session.add(new_question)

        db.session.commit()
        flash("Test created successfully!", "success")
        return redirect(url_for('view_tests'))

    return render_template('create_test.html')

@app.route('/view_tests')
@login_required
def view_tests():
    tests = Test.query.all() if current_user.role == "teacher" else Test.query.filter_by(teacher_id=current_user.id).all()
    return render_template('view_tests.html', tests=tests)

@app.route('/edit_test/<int:test_id>', methods=['GET', 'POST'])
@login_required
def edit_test(test_id):
    test = Test.query.get_or_404(test_id)
    
    if test.teacher_id != current_user.id:
        flash("You can only edit your own tests!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        test.title = request.form['title']
        db.session.commit()
        flash("Test updated successfully!", "success")
        return redirect(url_for('view_tests'))

    return render_template('edit_test.html', test=test)

@app.route('/delete_test/<int:test_id>', methods=['POST'])
@login_required
def delete_test(test_id):
    test = Test.query.get_or_404(test_id)

    if test.teacher_id != current_user.id:
        flash("You can only delete your own tests!", "danger")
        return redirect(url_for('dashboard'))

    db.session.delete(test)
    db.session.commit()
    flash("Test deleted successfully!", "success")
    return redirect(url_for('view_tests'))
