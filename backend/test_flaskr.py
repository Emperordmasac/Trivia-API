import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app, QUESTIONS_PER_PAGE
from models import setup_db, Question, Category, database_user, database_password


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}:{}@{}/{}".format(
            database_user, database_password, "localhost:5432", self.database_name
        )
        setup_db(self.app, self.database_path)
        self.new_question = {
            "question": "Who is the most influential person in the world",
            "answer": "elon musk",
            "difficulty": 2,
            "category": 4
        }
        self.new_question2 = {
            "answer": "I dont have a question nor category"
        }
        self.search = {
            "searchTerm": "title"
        }
        self.quiz = {
            "quiz_category": {"id": 2, "type": "Art"},
            "previous_questions": [9]
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    #====== UNITTEST FOR GET REQUEST ON CATEGORY======#

    def test_get_all_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['categories'])
        self.assertTrue(data['total_categories'])

    def test_404_categories_not_found(self):
        res = self.client().get('/categories/2')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Resource Not Found')

    #====== UNITTEST FOR GET REQUEST ON QUESTION======#

    def test_get_all_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertEqual(len(data['questions']), QUESTIONS_PER_PAGE)
        self.assertTrue(data['categories'])

    def test_404_questions_not_found(self):
        res = self.client().get('/questions?page=2000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Resource Not Found')

    #====== UNITTEST FOR GET DELETING A QUESTION======#

    def test_delete_specific_question(self):
        res = self.client().delete('/questions/2')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['deleted'])
        self.assertTrue(data['total_questions'])

    def test_422_deletion_unprocessable(self):
        res = self.client().delete('/questions/2000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Unprocessable")

    #====== UNITTEST FOR GET CREATING A QUESTION======#

    def test_add_new_question(self):
        res = self.client().post('/questions', json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['created'])

    def test_422_add_new_question_unprocessable(self):
        res = self.client().post("/questions", json=self.new_question2)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data['message'], "Unprocessable")

    #====== UNITTEST FOR GET SEARCHING FOR A QUESTION======#

    def test_search(self):
        res = self.client().post('/questions', json=self.search)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])

    #====== UNITTEST FOR GETTING QUESTIONS BASED ON CATEGORY ======#

    def test_get_questions_bycategory(self):
        res = self.client().get("/categories/2/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertEqual(data['current_category'], "Art")

    def test_404_get_questions_bycategory_not_found(self):
        res = self.client().get("/categories/200/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Resource Not Found")

    #====== UNITTEST FOR PLAYING THE QUIZ ======#

    def test_play_the_quiz(self):
        res = self.client().post('/quizzes', json=self.quiz)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['question'])
        self.assertNotEqual(data['question']['id'], 9)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
