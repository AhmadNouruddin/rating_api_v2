import os
import pandas as pd
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename


app = Flask(__name__, template_folder=os.getcwd())
app.secret_key = "secret key"

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def clean_data(csv_file):
    df = pd.read_csv(f'{csv_file}')

    # Cleaning prices from string and leaving only numbers
    for column in df.columns[df.columns.get_loc('Receiving call cost per min'):]:
        df[column] = pd.to_numeric(
            df[column], errors='coerce', downcast='float')

    # dealing with NaNs
    for index, row in df.iterrows():
        if not pd.isna(row['Company code']) and not pd.isna(row['Company number']):
            # fill NaN with 0
            df.fillna(0, inplace=True)
        else:
            # if Company code & Company number are NaN drop entire row
            new_df = df.drop(index)
    return new_df


def load_template_and_get_variables(row, round_decimal):
    content = {
        'region': row['Region'] if row else 'Region',
        'country': row['Country'] if row else 'Country',
        'company_name': row['Company name'] if row else 'Company name',
        'company_number': row['Company number'] if row else 'Company number',
        'company_code': row['Company code'] if row else 'Company code',
        'company_features': row['Company features'] if row else 'Company features',
        'receiving_call_cost_per_min': round(row['Receiving call cost per min'],
                                             round_decimal) if row else 'Receiving call cost per min',
        'local_call_cost_per_min': round(row['Local call cost per min'],
                                         round_decimal) if row else 'Local call cost per min',
        'calling_to_me_cost_per_min': round(row['Calling to ME cost per min'],
                                            round_decimal) if row else 'Calling to ME cost per min',
        'calling_to_other_destinations_cost_per_min': round(row['Calling to other destinations cost per min'],
                                                            round_decimal) if row else
        'Calling to other destinations cost per min',
        'sms_mo_cost_per_sms': round(row['SMS  MO cost per sms'],
                                     round_decimal) if row else 'SMS  MO cost per sms',
        'sms_mt_cost_per_sms': round(row['SMS MT cost per sms'],
                                     round_decimal) if row else 'SMS MT cost per sms',
        'data_cost_per_mb': round(row['Data cost per MB'],
                                  round_decimal) if row else 'Data cost per MB',
        'hpmn': 'HPMN',
        'effective_date': '2024',
        'submission_dt': 'SubmissionDT',
        'iot_identifier': 'IOTIdentifier',
        'correction_sequence': 'CorrectionSequence',
        'iot_currency': 'USD'}
    return content


@app.route('/', methods=['GET', 'POST'])
def upload_csv_file():
    if request.method == 'GET':
        return render_template('index.html')

    elif request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            resp = jsonify({'message': 'No file part in the request'})
            resp.status_code = 400
            return resp
        file = request.files['file']
        if file.filename == '':
            resp = jsonify({'message': 'No file selected for uploading'})
            resp.status_code = 400
            return resp
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            resp = jsonify({'message': 'File successfully uploaded'})
            resp.status_code = 201
            return resp
        else:
            resp = jsonify({'message': 'Allowed file type is csv'})
            resp.status_code = 400
            return resp


@app.route('/api/rating/<code>', methods=['GET'])
def rating_from_csv(code):
    if request.method == 'GET':
        for index, row in clean_data('Rating_Table.csv').iterrows():

            if code == row['Company code'].lower():
                content = load_template_and_get_variables(row, 2)
            file_name = f"RATING_XML_{content.get('company_code')}.xml"
        with open(file_name, 'w', encoding='utf8') as new_xml:
            new_xml.write(render_template('RATING_XML.xml', **content))
    return send_file(file_name, as_attachment=True, download_name=file_name)


@app.route('/api/rating', methods=['GET'])
def rating_without_csv():
    content = load_template_and_get_variables(None, 2)
    file_name = f"RATING_XML_{content.get('company_code')}.xml"
    with open(file_name, 'w', encoding='utf8') as new_xml:
        new_xml.write(render_template('RATING_XML.xml', **content))
    return send_file(file_name, as_attachment=True, download_name=file_name)


if __name__ == '__main__':
    app.run(debug=True)
