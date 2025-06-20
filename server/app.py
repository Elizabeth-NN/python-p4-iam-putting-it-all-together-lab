# #!/usr/bin/env python3

# from flask import request, session
# from flask_restful import Resource
# from sqlalchemy.exc import IntegrityError

# from config import app, db, api
# from models import User, Recipe

# class Signup(Resource):
#     pass

# class CheckSession(Resource):
#     pass

# class Login(Resource):
#     pass

# class Logout(Resource):
#     pass

# class RecipeIndex(Resource):
#     pass

# api.add_resource(Signup, '/signup', endpoint='signup')
# api.add_resource(CheckSession, '/check_session', endpoint='check_session')
# api.add_resource(Login, '/login', endpoint='login')
# api.add_resource(Logout, '/logout', endpoint='logout')
# api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


# if __name__ == '__main__':
#     app.run(port=5555, debug=True)


from flask import Flask, request, session, jsonify, make_response
from flask_restful import Api, Resource
from flask_migrate import Migrate
from models import db, User, Recipe
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

class Signup(Resource):
    def post(self):
        data = request.get_json()
        
        # Check for required fields
        required_fields = ['username', 'password', 'image_url', 'bio']
        errors = {}
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = [f"{field} is required"]
        
        if errors:
            return {'errors': errors}, 422
        
        try:
            new_user = User(
                username=data['username'],
                image_url=data['image_url'],
                bio=data['bio']
            )
            new_user.password_hash = data['password']
            db.session.add(new_user)
            db.session.commit()
            
            session['user_id'] = new_user.id
            
            return new_user.to_dict(), 201
        except ValueError as e:
            return {'errors': {'validation': [str(e)]}}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            return user.to_dict(), 200
        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(), 200
        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id')
            return {}, 204
        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        
        recipes = Recipe.query.all()
        return [{
            'id': recipe.id,
            'title': recipe.title,
            'instructions': recipe.instructions,
            'minutes_to_complete': recipe.minutes_to_complete,
            'user': recipe.user.to_dict(rules=('-recipes',))
        } for recipe in recipes], 200
    
    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        
        data = request.get_json()
        try:
            recipe = Recipe(
                title=data['title'],
                instructions=data['instructions'],
                minutes_to_complete=data['minutes_to_complete'],
                user_id=user_id
            )
            db.session.add(recipe)
            db.session.commit()
            
            return {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user': recipe.user.to_dict(rules=('-recipes',))
            }, 201
        except ValueError as e:
            return {'errors': str(e)}, 422

api.add_resource(Signup, '/signup')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(RecipeIndex, '/recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)