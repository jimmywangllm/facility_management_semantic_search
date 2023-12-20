##############
from flask import Flask
from apis import api

from flask import *
from flask_restx import *
from flask_session import *

import argsparser
args = argsparser.prepare_args()

app = Flask(__name__)

app.config.update(PROPAGATE_EXCEPTIONS=True)
api.init_app(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.run(
	host = '0.0.0.0', 
	port = 3073, 
	use_reloader = True)
##############