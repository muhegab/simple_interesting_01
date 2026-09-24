# simple_interesting_01
A simple and small website with a database and an access to AI chat window.

Prerequisites:
	* PostgreSQL
	* python3
	* Django
	* React
	* LangChain
	* LangGraph
	* All of the above can be replaced later with Docker.

To run the project:
	1. Start the backend server (Django then initialises the configured database, which is a database from PostgreSQL):
		python3 manage.py makemigrations
		python3 manage.py migrate
		python3 manage.py createsuperuser
		python3 manage.py runserver
		# Your Django API is now running at http://localhost:8000/api/tasks/. Visit it in your browser to confirm.
	2. Start the frontend server:
		npm start
		# React will run on http://localhost:3000. Because you configured CORS in Django, the frontend can now communicate with the backend.
		# The previous command starts also an nginx server on http://localhost:80
	3. Test the full stack:
		a. Open http://localhost:3000 in your browser.
		b. Add a task — it should appear in the list and be saved to PostgreSQL.
		c. Check http://localhost:8000/api/tasks/ to see the raw JSON data.
		d. You can also verify data in PostgreSQL:
			psql -h localhost -U user_01 -d projectdb_01 -c "SELECT * FROM api_task;"
			# password is "password_01"
	4. To test the LLM API from the backends side alone type the following in a terminal after running the backend server:
		curl -X POST http://localhost:8000/api/chat/ \
		-H "Content-Type: application/json" \
		-d '{"message": "Hello, what can you do?"}'

Project structure:
	myproject/
	├── backend/              # Django backend
	│   ├── api/              # Your Django app
	│   │   ├── models.py
	│   │   ├── serializers.py
	│   │   ├── views.py
	│   │   └── urls.py
	│   ├── backend/          # Django project settings
	│   │   ├── settings.py
	│   │   ├── urls.py
	│   │   └── wsgi.py
	│   └── manage.py
	└── frontend/             # React frontend
	    ├── src/
	    │   ├── App.js
	    │   ├── components/
	    │   └── services/
	    └── package.json
	    
Important Notes:
    CORS:
    	The django-cors-headers package is essential. Without it, your React app (port 3000) cannot communicate with Django (port 8000) due to browser security policies.
    Database migrations:
    	Every time you change a model, run python3 manage.py makemigrations and python3 manage.py migrate.
    Production:	
    	When deploying, set DEBUG = False, use environment variables for secrets, and configure ALLOWED_HOSTS properly.
    	

