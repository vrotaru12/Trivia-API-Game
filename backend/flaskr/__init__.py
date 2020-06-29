import os
from flask import Flask, jsonify, request, abort, json
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [q.format() for q in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)
    '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type,Authorization,true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''
    @app.route("/categories")
    def get_categories():
        categories = Category.query.order_by(Category.type).all()
        data = {}
        for index in categories:
            data[index.id] = index.type

        return jsonify({
            "success": True,
            "categories": data
        })

    @app.route('/questions')
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.order_by(Category.type).all()
        data = {}
        for index in categories:
            data[index.id] = index.type

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': data,
            'current_category': None,
        })

    @app.route('/questions/<int:q_id>', methods=['DELETE'])
    def delete_questions(q_id):
        try:
            question = Question.query.filter(Question.id == q_id).one_or_none()
            if question is None:
                abort(404)
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': q_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })
        except BaseException:
            abort(422)

    @app.route("/questions", methods=['POST'])
    def add_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })
        except BaseException:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        search = body.get('searchTerm', None)

        if search:
            results = Question.query.filter(
                Question.question.ilike(f'%{search}%')).all()
            data = [question.format() for question in results]

            return jsonify({
                'success': True,
                'questions': data,
                'total_questions': len(results),
                'current_category': None
            })
        abort(404)

    @app.route('/categories/<int:category>/questions', methods=['GET'])
    def get_question_by_category(category):
        selection = Question.query.filter(Question.category == category)
        listTab = []
        for i in selection:
            listTab.append(i.format())

        if selection is None:
            abort(404)

        return jsonify({
            'success': True,
            'questions_by_category': listTab,
            'total_questions_categorised': len(listTab)
        })

    @app.route('/quizzes', methods=['POST'])
    def create_q_with_given_categ():
        try:
            body = request.get_json()
            category = body.get('quiz_categ')
            previous_q = body.get('previous_q')
            if ('quiz_categ' in body and 'previous_q' in body):
                # when 'all' is clicked
                if category['type'] == 'click':
                    retrieved_q = Question.query.filter(
                        Question.id.notin_((previous_q))).all()
                else:
                    # when a specific category is selected
                    retrieved_q = Question.query.filter_by(
                        category=category['id']).filter(
                        Question.id.notin_(
                            (previous_q))).all()
                length_of_available_question = len(retrieved_q)

                if length_of_available_question > 0:
                    data = retrieved_q[random.randrange(
                        0, length_of_available_question)].format()
                    result = {
                        "success": True,
                        "question": data
                    }
                else:
                    result = {
                        "success": True,
                        "question": None
                    }
                return jsonify(result)
            else:
                abort(422)
        except BaseException:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource Not found"
        }), 404

    @app.errorhandler(422)
    def unprocesable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocesable"
        }), 422

    @app.errorhandler(500)
    def unprocesable(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500

    @app.errorhandler(400)
    def unprocesable(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"
        }), 400

    return app
