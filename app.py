from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import io

app = Flask(__name__)

# Define the correct column order
COLUMN_ORDER = ['ID', 'task_name', 'task_describe', 'task_type', 'software_for_task', 'output', 'tool_id']

# Load data from CSV file
df = pd.read_csv('task.csv')
# Ensure the dataframe has all required columns in the correct order
df = df.reindex(columns=COLUMN_ORDER)
# Add an index column to maintain original order
df['original_index'] = range(len(df))

@app.route('/')
def index():
    task_types = df['task_type'].unique().tolist()
    return render_template('index.html', data=df[COLUMN_ORDER].to_dict('records'), task_types=task_types)

@app.route('/filter', methods=['POST'])
def filter_data():
    filters = request.json
    filtered_df = df.copy()

    if filters['keyword']:
        filtered_df = filtered_df[filtered_df.apply(lambda row: filters['keyword'].lower() in row.astype(str).str.lower().values.any(), axis=1)]
    
    if filters['task_type']:
        filtered_df = filtered_df[filtered_df['task_type'] == filters['task_type']]
    
    if filters['task_name']:
        filtered_df = filtered_df[filtered_df['task_name'].str.contains(filters['task_name'], case=False)]

    # Sort by the original index to maintain order
    filtered_df = filtered_df.sort_values('original_index')
    
    # Return only the specified columns in the correct order
    return jsonify(filtered_df[COLUMN_ORDER].to_dict('records'))

@app.route('/export_csv')
def export_csv():
    output = io.StringIO()
    df[COLUMN_ORDER].to_csv(output, index=False)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='export.csv')

@app.route('/export_excel')
def export_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df[COLUMN_ORDER].to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name='export.xlsx')

@app.route('/import_csv', methods=['POST'])
def import_csv():
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and file.filename.endswith('.csv'):
        global df
        df = pd.read_csv(file)
        # Ensure the imported data has all required columns in the correct order
        df = df.reindex(columns=COLUMN_ORDER)
        # Add an index column to maintain original order for the new data
        df['original_index'] = range(len(df))
        return jsonify(df[COLUMN_ORDER].to_dict('records'))
    else:
        return jsonify({'error': 'Invalid file format'})

if __name__ == '__main__':
    app.run(debug=True)