from flask_socketio import emit, send
from .. import socketio
from .. import models, data


@socketio.on('slider_changed')
def handle_slider_changed(info):
    """Updating plot due to change in data"""
    print("Emitting plot update")
    new_value = info['newValue']
    var_definition = info['definition']
    var_idx = data.model_vars_text.index(var_definition)
    var = data.model_vars[var_idx]
    emit('data_updated', {'variable': var, 'new_value': new_value, 'index': var_idx})

@socketio.on("model_update")
def handle_model_update(info):
    """Updating model due to change in data"""
    print("Emitting model update")
    new_value = info['newValue']
    var = info['variable']
    area = info['area']

    data.update_data(area, var, new_value)

    emit("model_update", {})

@socketio.on('connect')
def test_connect():
    print("Connection succesful")