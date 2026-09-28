import os
import boto3
import pymysql
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# AWS S3 configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

s3 = boto3.client("s3", region_name=AWS_REGION)


# MySQL database connection
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "studentdb"),
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    course = request.form.get("course")
    photo = request.files.get("photo")

    if not name or not email or not course:
        return "Please fill in all required fields."

    photo_url = ""

    if photo and photo.filename:
        filename = secure_filename(photo.filename)

        s3.upload_fileobj(
            photo,
            S3_BUCKET_NAME,
            filename,
            ExtraArgs={
                "ContentType": photo.content_type
            }
        )

        photo_url = (
            f"https://{S3_BUCKET_NAME}.s3."
            f"{AWS_REGION}.amazonaws.com/{filename}"
        )

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO students
                (name, email, course, photo_url)
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(
                sql,
                (name, email, course, photo_url)
            )

        connection.commit()

    finally:
        connection.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
