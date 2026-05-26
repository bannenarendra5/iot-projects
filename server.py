from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import uuid
import qrcode
from io import BytesIO
import base64
import firebase_admin
from firebase_admin import credentials, db
import time

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://came-c5012-default-rtdb.firebaseio.com/'  # Replace with your Firebase URL
})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

@app.route('/api/generate-qr', methods=['POST'])
def generate_qr():
    data = request.json
    panel_name = data.get('name')
    switches = data.get('switches', [])
    
    if not panel_name or not switches:
        return jsonify({'error': 'Panel name and switches are required'}), 400
    
    # Create a unique ID for the panel
    panel_id = str(uuid.uuid4())[:8]
    
    # Create switch data - simplified structure
    switch_data = {}
    for i, switch in enumerate(switches):
        switch_data[str(i)] = {
            'name': switch,
            'state': False
        }
    
    # Save to Firebase
    panel_ref = db.reference(f'panels/{panel_id}')
    panel_ref.set({
        'name': panel_name,
        'switches': switch_data,
        'created': int(time.time() * 1000)
    })
    
    # Generate QR code with panel ID
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(panel_id)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code to memory
    buffer = BytesIO()
    img.save(buffer)
    buffer.seek(0)
    
    # Convert to base64 for embedding in HTML
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    qr_data_uri = f"data:image/png;base64,{qr_base64}"
    
    return jsonify({
        'panelId': panel_id,
        'qrCodeUrl': qr_data_uri
    })

@app.route('/api/panel/<panel_id>')
def get_panel(panel_id):
    panel_ref = db.reference(f'panels/{panel_id}')
    panel_data = panel_ref.get()
    
    if not panel_data:
        return jsonify({'error': 'Panel not found'}), 404
    
    return jsonify(panel_data)

@app.route('/api/update-switch', methods=['POST'])
def update_switch():
    data = request.json
    panel_id = data.get('panelId')
    switch_id = data.get('switchId')
    new_state = data.get('state')
    
    if None in [panel_id, switch_id] or new_state is None:  # Fixed to check if new_state is None
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Update switch state in Firebase - simplified structure
        #switch_ref = db.reference(f'panels/{panel_id}/switches/{switch_id}/state')
        switch_ref = db.reference(f'switches/{switch_id}/state')
        switch_ref.set(new_state)
        
        return jsonify({'success': True, 'state': new_state})  # Return the new state in response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)