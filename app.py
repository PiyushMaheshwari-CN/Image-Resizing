from flask import Flask, render_template, request, send_file
import boto3
import os
import uuid

app = Flask(__name__)

s3 = boto3.client('s3')

SOURCE_BUCKET = "image-upload-source-bucket-n"
DEST_BUCKET = "image-resized-destination-bucket-n"

SOURCE_FOLDER = "source-folder/"
DOWNLOAD_FOLDER = "downloads/"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


# -------- SECTION 1: Resize --------
@app.route('/resize', methods=['POST'])
def resize():
    file = request.files['image']
    width = request.form['width']
    height = request.form['height']

    filename = f"{uuid.uuid4()}_{file.filename}"
    local_path = os.path.join(DOWNLOAD_FOLDER, filename)
    file.save(local_path)

    s3.upload_file(
        local_path,
        SOURCE_BUCKET,
        SOURCE_FOLDER + filename,
        ExtraArgs={
            "Metadata": {
                "width": width,
                "height": height
            }
        }
    )

    return render_template('index.html', resized_file=filename)


# -------- SECTION 2: Restore --------
@app.route('/restore', methods=['POST'])
def restore():
    file = request.files['image']
    filename = file.filename
    temp_path = os.path.join(DOWNLOAD_FOLDER, filename)
    file.save(temp_path)

    s3.upload_file(
        temp_path,
        DEST_BUCKET,
        filename
    )

    return render_template('index.html', message="Restore request sent")


# -------- Download resized image --------
@app.route('/download/<filename>')
def download(filename):
    local_file = os.path.join(DOWNLOAD_FOLDER, filename)

    s3.download_file(DEST_BUCKET, filename, local_file)

    return send_file(local_file, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
