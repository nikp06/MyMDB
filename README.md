# MyMDB
MyMDB - My Movie Database - is a web application for managing movie ratings/wishlists/thougths and getting inspiration for new movies along the way

## About MyMDB

Hello Internet! Welcome to *MyMDB - My Movie Database*, which is the result of my final project for [Harvard's CS50x](https://cs50.harvard.edu/x/2020/) introduction to computer science. *MyMDB* was created out of my passion for movies and is an online application, that will help you to organize your past and future movie experiences. It relies on the huge movie database that has been made available by [IMDb](https://www.imdb.com/) for non-commercial use.

With my application *MyMDB* you can create your personal database, which then serves as a sort of library with which you, as a registered user, can manage your personal ratings and notes you stored for a particular movie. A personal watchlist is there for you to keep track of movies you always wanted to watch but haven't had the time to yet.

Once you have amassed some data about your movie preferences this application allows you to play around with IMDb's and your own statistics.

For instance, you can let a simple algorithm pick movie recommendations with directors and stars that also produced or starred in some of your favourite movies.

Another fun thing is just to browse through the huge database of **344,276 movies from 1970 until 2020 and 1,044,499 actors/actresses and directors**.

With the search function of this Web Application you can filter your queries by Title and Director's or Star's names. So you can be very specific and find the exact movie you are looking for or you could just search for all movies that are produced by a guy named John and/or are from the year 2004. 

A Randomizer will give you inspiration for new movie ideas by just randomly skimming through the database on different keys you provide. You could randomize a movie by a given year, director or star and in turn get a movie that you otherwise might have never heard of.

Dynamically created links can be clicked on each movie title that will appear on the website to see the particular movie with even more information on IMDb's own page of that movie.

With *MyMDB* you explore IMDb's world of movies with fun and create your personal movie album along the way.

## Description

This Web application is based on the Flask framework. It makes use of jQuery and JavaScript to dynamically alter the DOM and communicate with the backend where the [cs50 python lib](https://github.com/cs50/python-cs50) is used for working with the database. It can be downloaded from github or replaced with something like SQLite. CSS and the Bootstrap library are used for the styling of the page. 

## How to use

I have debugged and tested my application in CS50ide so I can't really explain how to run *MyMDB* other than by simply using the following command from the project directory:

```
$ flask run
```

## Requirements

- python 3
- flask
- cs50 (for sqlite queries)
- werkzeug (for error handling and safe password generation)
