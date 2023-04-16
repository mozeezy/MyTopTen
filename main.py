from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


movie_db_url = "https://api.themoviedb.org/3/search/movie"


app = Flask(__name__)
app.app_context().push()
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)
    img_url = db.Column(db.Text, nullable=True)


db.create_all()


class RateMovieForm(FlaskForm):
    your_rating = StringField(label="Your Rating Out of 10 (e.g. 7.5)", validators=[DataRequired()])
    your_review = StringField(label="Your Review", validators=[DataRequired()])
    done_btn = SubmitField(label="Submit")


class AddMovieForm(FlaskForm):
    title = StringField(label="Movie Title")
    submit = SubmitField(label="Add Movie")


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for n in range(len(all_movies)):
        all_movies[n].ranking = len(all_movies) - n
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    movie_id = request.args.get("movie_id")
    edit_form = RateMovieForm()
    selected_movie = Movie.query.get(movie_id)
    if edit_form.validate_on_submit():
        selected_movie.rating = float(edit_form.your_rating.data)
        selected_movie.review = edit_form.your_review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=edit_form, selected_movie=selected_movie)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie_id = request.args.get("movie_id")
    movie_to_be_deleted = Movie.query.get(movie_id)
    db.session.delete(movie_to_be_deleted)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    add_form = AddMovieForm()
    if add_form.validate_on_submit():
        api_response = requests.get(movie_db_url, params={"api_key": os.environ.get("API_KEY"), "query": add_form.title.data}).json()["results"]
        return render_template("select.html", movies=api_response)
    return render_template("add.html", form=add_form)


@app.route("/find_movie")
def find_movie():
    movie_id_from_api = request.args.get("id")
    if movie_id_from_api:
        movie_api_url = f"https://api.themoviedb.org/3/movie/{movie_id_from_api}"
        response = requests.get(movie_api_url, params={"api_key": os.environ.get("API_KEY")}).json()
        new_movie = Movie(
            title=response["original_title"],
            year=response["release_date"].split("-")[0],
            img_url=f"https://image.tmdb.org/t/p/w500{response['poster_path']}",
            description=response["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
