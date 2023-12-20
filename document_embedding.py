##############document_embedding.py##############
import re 
import os 
import pandas as pd
import numpy as np
import requests


def document_split(
	document_content,
	fragment_window_size = 5,
	fragment_step_size = 4,
	sentence_left_context_size = 2,
	sentence_right_context_size = 5,
	):

	# sentence segmentation
	response = requests.post(
	'http://37.224.68.132:27331/stanza/sentence_segmentation',
	json = {'text':document_content}
	)
	response_data = response.json()
	sentences = response_data['sentences']

	## prompts to get questions
	prompts = []

	# setence to fragements
	fragments = []

	start_sentence_idx = 0
	while(start_sentence_idx+fragment_window_size <= len(sentences)):
		fragment = sentences[start_sentence_idx:start_sentence_idx+fragment_window_size]
		fragment = ' '.join(fragment)
		start_sentence_idx += fragment_step_size
		fragments.append(fragment)

	'''
	fragment_window_size = 3
	fragment_step_size = 1
	start_sentence_idx = 0
	while(start_sentence_idx+fragment_window_size <= len(sentences)):
		fragment = sentences[start_sentence_idx:start_sentence_idx+fragment_window_size]
		fragment = ' '.join(fragment)
		start_sentence_idx += fragment_step_size
		fragments.append(fragment)
	'''

	# fragements to prompts
	for f in fragments:
		prompt = f"""
<s> [INST] <<SYS>> Read the following document and generate questions from its content. The question should be self-contained and complete. The generated questions are in the format of:

Q:
Q:
Q:
...

Do not generate answers. Do not include the phrase "according to the document..." or "according to the author" in the question. Each question should be shorter than 50 words.

<</SYS>>

document: {f}
[/INST] Sure. Here are the generated questions:
	"""
		prompts.append(prompt.strip())

	# prompts to questions

	output = []

	## llama-2
	response = requests.post(
		'http://37.224.68.132:27465/llm/llama_2_7b_batch',
		json = {
		'prompts':prompts,
		'max_tokens':1024
		}
		)

	for f, q in zip(
		fragments,
		response.json()['responses']
		):
		output.append({
			'fragement':f,
			'searchable_text':f,
			'searchable_text_type': 'fragement',
		})
		for m in re.finditer(r'Q:\s*(?P<question>[^\n].*?)(\n|$)', q):
			output.append({
				'fragement':f,
				'searchable_text':m.group('question'),
				'searchable_text_type': 'fragment_question_by_llama_2',
			})


	## mistral
	response = requests.post(
		'http://37.224.68.132:27464/llm/mistral_7b_batch',
		json = {
		'prompts':prompts,
		'max_tokens':1024
		}
		)

	for f, q in zip(
		fragments,
		response.json()['responses']
		):
		output.append({
			'fragement':f,
			'searchable_text':f,
			'searchable_text_type': 'fragement',
		})
		for m in re.finditer(r'Q:\s*(?P<question>[^\n].*?)(\n|$)', q):
			output.append({
				'fragement':f,
				'searchable_text':m.group('question'),
				'searchable_text_type': 'fragment_question_by_mistral',
			})

	### sentences
	sentence_num  = len(sentences)

	## sentence level question
	for i in range(sentence_num):
		sentence = sentences[i]
		sentence_en = re.sub(r'[^A-z]+', r'', sentence)
		if len(sentence_en) > 16:
			start_idx = np.max([0, i-sentence_left_context_size])
			end_idx = np.min([sentence_num, i+sentence_right_context_size])
			fragment = sentences[start_idx:end_idx]
			fragment = ' '.join(fragment)
			output.append({
				'fragement':fragment,
				'searchable_text':sentence,
				'searchable_text_type': 'sentence',
			})

	return output


###########

def document_embedding(
	documents,
	batch_size = 100
	):

	batch_num = len(documents)/batch_size

	for i in range(int(batch_num)+1):
		try:
			texts = [d['searchable_text'] for d in documents[i*batch_size: (i+1)*batch_size]]
			embedding_vectors = requests.post(
			'http://37.224.68.132:27333/text_embedding/all_MiniLM_L6_v2',
			json  = {
			"texts": texts
			}).json()['embedding_vectors']
			j = 0
			for r in documents[i*batch_size: (i+1)*batch_size]:
				r['searchable_text_embedding'] = embedding_vectors[j]
				j += 1
		except:
			pass

	return documents


def document_search(
	query_text,
	document_embeddings,
	):


	#print(document_embeddings_current)

	query_text_embedding = requests.post(
	'http://37.224.68.132:27333/text_embedding/all_MiniLM_L6_v2',
	json  = {
	"texts": [query_text]
	}).json()['embedding_vectors'][0]

	#print(document_embeddings_current)

	document_embeddings_current = []

	for r in document_embeddings:
		try:
			r_current = r
			r_current['score'] = np.dot(
				np.array(query_text_embedding), 
				np.array(r_current['searchable_text_embedding']))
			document_embeddings_current.append(r_current)
		except:
			pass

	document_embeddings_sorted = sorted(
		document_embeddings_current, 
		key=lambda d: d['score'], 
		reverse=True)

	return document_embeddings_sorted[0]

##############document_embedding.py##############