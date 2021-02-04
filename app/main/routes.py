import json
import os
from decimal import Decimal

import numpy as np
import pandas as pd
from app import data, models, plots
from flask import jsonify, render_template, request

from . import main


@main.route('/', methods=['GET'])
def index():
	return render_template("home.html")


@main.route('/bokeh', methods = ['GET', 'POST'])
def bokeh():
	# Query params in URL
	queryParams = {}
	queryParams["property_type"] = request.args.get("property_type") or 'WCORHUUR_P'
	queryParams["rental_price"] = request.args.get("rental_price") or 'WHUURTSLG_P'
	queryParams["surface_area"] = request.args.get("surface_area") or 'WOPP0040_P'

	return render_template("bokeh.html", queryParams=queryParams, data=data)


@main.route("/data", methods=['GET'])
def get_data():
	"""Returns some JSON.
	Example:
	{
		area_changed_proba: null
		plotData: {doc: {…}, root_id: "1537", target_id: "myplot"}
		prediction: "Noord-Oost"
		prediction_proba: "0.145"	
	}
	"""
	# Query params in URL
	queryParams = {}
	queryParams["area"] = request.args.get("area")
	queryParams["property_type"] = request.args.get("property")
	queryParams["rental_price"] = request.args.get("price")
	queryParams["surface_area"] = request.args.get("surface")
	queryParams["plot"] = request.args.get("plot")

	def to_model_input_vars(surface_area, rental_price, property_type):
		query_input = []
		for index, var in enumerate([
			queryParams["surface_area"], queryParams["rental_price"], queryParams["property_type"]
		]):
			vars_query_input = [0] * len(data.all_var_types[index])
			idx_query_var = data.all_var_types[index].index(var)
			vars_query_input[idx_query_var] = 100
			query_input.extend(vars_query_input)

		# reshape query_input to correct format for input to our model
		model_input_vars = np.array(query_input).reshape(1, -1)
		return model_input_vars

	model_input_vars = to_model_input_vars(
		queryParams["surface_area"], 
		queryParams["rental_price"], 
		queryParams["property_type"]
	)

	# retrain model based on new data
	trained_model = models.train_model(data.model_data, data.area_names, data.model_vars)

	# have our trained model make a prediction based on our query input
	_, probabilities = models.pred_proba(model=trained_model, input_vars=model_input_vars)
	pred_area_index = np.where(probabilities[0] == np.amax(probabilities[0]))
	pred_area_index = pred_area_index[0][0]
	
	# determine the index of the predicted area within the returned probabilities array
	predicted_area = data.area_names[pred_area_index]
	area_prob = probabilities[0][pred_area_index]
	area_prob = '%.3f' % Decimal(area_prob)

	# determine how the prediction probability of our previously predicted area has changed 
	# due to the change in data variables of this area
	if queryParams["area"] is not None:
		pred_area_index = data.area_names.index(queryParams["area"])
		new_proba_prev_area = probabilities[0][pred_area_index]
		new_proba_prev_area = '%.3f' % Decimal(new_proba_prev_area)
		area_name = queryParams["area"]
	else:
		new_proba_prev_area = None
		area_name = predicted_area

	del probabilities
		
	if queryParams["plot"] is not None:
		plot_data = data.model_data.loc[data.model_data['area_name'] == area_name]
		plot_data = plot_data.loc[:, data.model_vars]
		queryParams["plot"] = plots.create_hbar(area_name, plot_data)
		print("pred_area", predicted_area)
		print("area_prob", area_prob)
		print("new_proba_prev_area", new_proba_prev_area)
		return jsonify(
			prediction=predicted_area, 
			prediction_proba=area_prob, 
			area_changed_proba=new_proba_prev_area, 
			plotData=queryParams["plot"]
		)
	else:
		return jsonify(
			prediction=predicted_area, 
			prediction_proba=area_prob, 
			area_changed_proba=new_proba_prev_area
		)


@main.route('/d3', methods = ['GET'])
def d3():
	area_name = request.args.get("area_name")

	if area_name is None:
		area_name = "Centrum-West"

	plot_data = data.stats_ams.loc[data.stats_ams['area_name'] == area_name]
	plot_data = plot_data.drop(['area_name', 'area_code'], axis=1)
	plot_data = plot_data.to_json(orient='records')

	meta_data = data.stats_ams_meta.to_json(orient='records')
	return render_template("d3.html", meta_data=meta_data,
		x_variables=data.model_vars, area_names=data.area_names, selected_area_name=area_name)


@main.route('/d3_plot_data', methods = ['GET'])
def d3_plot_data():
	area_name = request.args.get("area_name")

	plot_data = data.stats_ams.loc[data.stats_ams['area_name'] == area_name]
	plot_data = plot_data.drop(['area_name', 'area_code'], axis=1)
	plot_data = plot_data.to_json(orient='records')

	return plot_data
