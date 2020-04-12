# Project 1

Web Programming with Python and JavaScript

Overview
In this project, you’ll build a book review website. Users will be able to register for your website and then log in using their username and password. Once they log in, they will be able to search for books, leave reviews for individual books, and see the reviews made by other people. You’ll also use the a third-party API by Goodreads, another book review website, to pull in ratings from a broader audience. Finally, users will be able to query for book details and book reviews programmatically via your website’s API.

application.py

All the code related to the back end of the page using flask. Here the queries of sql are made and functions for the programmatically

books.csv
a csv file with the book contained in the db

helpers.py
functions that help the application.py. Here is one that make easier the login_required

import.py
How the csv file was imported in the db

book.html
Page book where are the details of the searched book and where you can make a review

index.html
Index of the page to login or Register

layout.html
layoutof the pages

login.html
page to login

mistake.html
page that tells you when you have a mistake in the introduction of data in the forms

register.html
page to register a new users

search.html
page to search for books per title author or isbns

searched.html
list of books founded in the search 
