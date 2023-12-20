##############server_path.py##############

import time
import logging
import argsparser
from flask_restx import *
from flask import *

from document_embedding import *
import pandas as pd
import hashlib


duna_embedding_file = '/data/home/jim.wang/rag_ui_3072/document_embeddings_df.json'


document_embeddings = pd.read_json(
'document_embeddings_df.json',
lines = True,
orient = 'records').to_dict('records')

ns = Namespace(
	'facility_management_qa', 
	description='Facility Management QA',
	)

args = argsparser.prepare_args()

#############

semantic_search_parser = ns.parser()
semantic_search_parser.add_argument('question', type=str, location='json')

semantic_search_inputs = ns.model(
	'facility_management_qa', 
		{
			'question': fields.String(example = u"What is the supplier duty?")
		}
	)

@ns.route('/semantic_search')
class semantic_search_api(Resource):
	def __init__(self, *args, **kwargs):
		super(semantic_search_api, self).__init__(*args, **kwargs)
	@ns.expect(semantic_search_inputs)
	def post(self):		
		start = time.time()
		try:			
			args = semantic_search_parser.parse_args()		
			output = {}		
			output['question'] = args['question']

			query_result = document_search(
				query_text = args['question'],
				document_embeddings = document_embeddings,
				)

			###
			if query_result['score'] > 0.7:
				output['document_fragment'] = query_result['fragement']
				output['document_name'] = query_result['file_name']
				output['score'] = query_result['score']
			else:
				output['document_fragment'] = None
				output['document_name'] = None
				output['score'] = None

			output['status'] = 'success'
			output['running_time'] = float(time.time()- start)
			return output, 200
		except Exception as e:
			output = {}
			output['status'] = str(e)
			output['running_time'] = float(time.time()- start)
			return output

################


semantic_search_updated_by_duna_parser = ns.parser()
semantic_search_updated_by_duna_parser.add_argument('question', type=str, location='json')

semantic_search_updated_by_duna_inputs = ns.model(
	'facility_management_qa', 
		{
			'question': fields.String(example = u"What is the supplier duty?")
		}
	)

@ns.route('/semantic_search_updated_by_duna')
class semantic_search_updated_by_duna_api(Resource):
	def __init__(self, *args, **kwargs):
		super(semantic_search_updated_by_duna_api, self).__init__(*args, **kwargs)
	@ns.expect(semantic_search_updated_by_duna_inputs)
	def post(self):		
		start = time.time()


		try:

			## check the md5 and compare to the session
			document_embeddings_md5_current = hashlib.md5(open(duna_embedding_file,'rb').read()).hexdigest()

			try:
				document_embeddings_md5 = session.get("document_embeddings_md5")
			except:
				# if it is the first time, load the file
				document_embeddings_md5 = document_embeddings_md5_current
				document_embeddings_updated_by_duna = pd.read_json(
				duna_embedding_file,
				lines = True,
				orient = 'records').to_dict('records')
				session["document_embeddings_updated_by_duna"] = document_embeddings_updated_by_duna
				session["document_embeddings_md5"] = document_embeddings_md5_current

			if document_embeddings_md5_current != document_embeddings_md5:
				# if changed, reload the file
				document_embeddings_updated_by_duna = pd.read_json(
				duna_embedding_file,
				lines = True,
				orient = 'records').to_dict('records')
				session["document_embeddings_updated_by_duna"] = document_embeddings_updated_by_duna
				session["document_embeddings_md5"] = document_embeddings_md5_current

			args = semantic_search_updated_by_duna_parser.parse_args()		
			output = {}		

			output['question'] = args['question']

			query_result = document_search(
				query_text = args['question'],
				document_embeddings = session["document_embeddings_updated_by_duna"],
				)

			###
			if query_result['score'] > 0.7:
				output['document_fragment'] = query_result['fragement']
				output['document_name'] = query_result['file_name']
				output['score'] = query_result['score']
			else:
				output['document_fragment'] = None
				output['document_name'] = None
				output['score'] = None

			output['status'] = 'success'
			output['running_time'] = float(time.time()- start)
			return output, 200
		except Exception as e:
			output = {}
			output['status'] = str(e)
			output['running_time'] = float(time.time()- start)
			return output


##############server_path.py##############
