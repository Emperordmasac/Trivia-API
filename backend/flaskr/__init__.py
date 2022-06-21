from distutils.log import error
from errno import errorcode
import os
from unicodedata import category
from flask import Flask, request, abort, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import sys

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10


def questions_pagination(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type, Authorization, True"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    """
    GET ALL CATEGORIES ENDPOINT
    """
    @app.route('/categories')
    def get_all_categories():
        error = False
        try:
            categories = Category.query.order_by(Category.id).all()
        except:
            error = True
            flash('An error occured getting list of categories')
            print(sys.exc_info())
        finally:
            if error:
                abort(404)
            else:
                return jsonify({
                    'success': True,
                    'categories': {category.id: category.type for category in categories},
                    'total_categories': len(categories)
                })

    """ 
    GET ALL QUESTIONS ENDPOINT
    """

    @app.route('/questions')
    def get_all_questions():
        error = False
        try:
            categories_selection = Category.query.order_by(Category.id).all()
            questions_selection = Question.query.order_by(Question.id).all()
            questions = questions_pagination(request, questions_selection)

            if len(questions) == 0:
                abort(404)

        except:
            error = True
            flash('An error occured getting list of questions')
            print(sys.exc_info())
        finally:
            if error:
                abort(404)
            else:
                return jsonify({
                    'success': True,
                    'questions': questions,
                    'total_questions': len(questions_selection),
                    'current_category': categories_selection[0].type,
                    'categories': {category.id: category.type for category in categories_selection},

                })

    """
    DELETE A QUESTION ENDPOINT
    """

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_specific_question(question_id):
        error = False
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            questions_selection = Question.query.order_by(Question.id).all()
            questions = questions_pagination(request, questions_selection)
        except:
            db.session.rollback()
            error = True
            print(sys.exc_info())
            flash('Error deleteing the specified question. TRY AGAIN!')
        finally:
            db.session.close()
            if error:
                abort(422)
            else:
                return jsonify({
                    'success': True,
                    'questions': questions,
                    'deleted': question_id,
                    'total_questions': len(questions)
                })
    """
    ADD NEW QUESTION ENDPOINT
    """
    @app.route('/questions', methods=['POST'])
    def add_new_question():
        error = False
        body = request.get_json()

        new_category = body.get('category', 1)
        new_question = body.get('question', '')
        new_answer = body.get('answer', '')
        new_difficulty = body.get('difficulty', 4)
        search_term = body.get('searchTerm', None)

        if (new_question == '' or new_answer == '') and search_term is None:
            abort(422)

        try:
            if search_term:
                questions_selection = Question.query.order_by(
                    Question.id).filter(Question.question.ilike("%{}%".format(search_term))).all()
                questions = questions_pagination(request, questions_selection)

                return jsonify({
                    'success': True,
                    'questions': questions,
                    'total_questions': len(questions_selection)
                })
            else:
                question = Question(category=new_category,
                                    question=new_question, answer=new_answer, difficulty=new_difficulty)
                question.insert()

                questions_selection = Question.query.order_by(
                    Question.id).all()
                questions = questions_pagination(request, questions_selection)

                return jsonify({
                    'success': True,
                    'questions': questions,
                    'total_questions': len(questions_selection),
                    'created': question.id
                })
        except:
            db.session.rollback()
            print(sys.exc_info())
            abort(422)
        finally:
            db.session.close()

    """
    @TODO:
    QUESTIONS BY CATEGORY ENDPOINT
    """

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_bycategory(category_id):
        error = False
        try:
            category = Category.query.filter(
                Category.id == category_id).one_or_none()

            if category is None:
                abort(404)

            questions_selection = Question.query.order_by(
                Question.id).filter(Question.category == category_id).all()
            questions = questions_pagination(request, questions_selection)

        except:
            error = True
            print(sys.exc_info())
        finally:
            if error:
                abort(404)
            else:
                return jsonify({
                    'success': True,
                    'questions': questions,
                    'total_questions': len(questions_selection),
                    'current_category': category.type
                })

    """
    QUIZZES ENDPOINT
    """

    @app.route('/quizzes', methods=['POST'])
    def play_the_quiz():
        error = False
        body = request.get_json()
        quiz_category = body.get('quiz_category')
        previous_questions = body.get('previous_questions')
        try:
            if quiz_category is None or quiz_category['id'] == 0:
                category_questions = Question.query.all()
            else:
                category_questions = Question.query.filter(
                    Question.category == quiz_category['id'])

            random_question = random.choice(
                [question for question in category_questions if question.category not in previous_questions])

            question = {
                'id': random_question.id,
                'question': random_question.question,
                'answer': random_question.answer,
                'category': random_question.category,
                'difficulty': random_question.difficulty
            }
        except:
            error = True
            print(sys.exc_info())
        finally:
            if error:
                abort(422)
            else:
                return jsonify({
                    'success': True,
                    'question': question,
                    'previous_questions': previous_questions
                })

    """
    ERROR HANDLERS
    """
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource Not Found",
        }), 404

    @app.errorhandler(405)
    def method_not_found(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method Not Allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422

    @app.errorhandler(500)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Internal Server Error"
        }), 500

    return app
