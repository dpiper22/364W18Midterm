###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SubmitField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
import json

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

manager = Manager(app)
## All app.config values
app.config['SECRET_KEY'] = 'si364hardtoguesssecretkey'

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost/djpipermidtermdb"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


#error handling route

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
######################################
######## HELPER FXNS (If any) ########
######################################




##################
##### MODELS #####
##################
#referenced https://github.com/SI364-Winter2018/Discussion-Playlists_GetOrCreate/blob/master/main_app.py for start of setting up models with relationships


class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    review = db.Column(db.String(300))
    bussiness_id = db.Column(db.Integer, db.ForeignKey('businesses.id'))

    def __repr__(self):
        return "Review {} | bussiness_id {} (ID: {})".format(self.review, self.bussiness_id, self.id)

class Business(db.Model):
    __tablename__ = "businesses"
    id = db.Column(db.Integer, primary_key = True)
    business_name = db.Column(db.String(100), unique = True)
    location = db.Column(db.String(100))
    price = db.Column(db.String(4))
    rating = db.Column(db.Integer)
    review = db.relationship('Review', backref='Business')
    def __repr__(self):
        return "{}: Location: {}, Price: {}, Rating: {} out of five stars, Review: {} (ID: {})".format(self.name, self.location, self.price, self.rating, self.review, self.id)


class Returns(db.Model):
    __tablename__ = "return_to_business"
    id = db.Column(db.Integer, primary_key = True)
    business_name = db.Column(db.String(100))
    goback = db.Column(db.String(3))
    reason = db.Column(db.String(300))

    def __repr__(self):
        return "Would you go back to {}? {}. Why or why not? {} (ID: {})".format(self.business_name, self.goback, self.reason, self.id)




###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name.",validators=[Required()])
    business = StringField("Please enter a business you would like to review.",validators=[Required()])
    review = StringField("Please leave a review of this business. Did you have a positive experience? Was the Staff Friendly?", validators=[Required()])
    submit = SubmitField()

#class ReviewForm(FlaskForm):
 #   name = StringField("Please enter your name.",validators=[Required()])
#  business = StringField("Please enter a business you would like to review.",validators=[Required()])
 #   review = StringField("Please leave a review of this business. Did you have a positive experience? Was the Staff Friendly?", validators=[Required()])

class BusinessForm(FlaskForm):
    business_name = StringField("Please enter a business to rate.",validators=[Required()])
    location = StringField("Please enter the location of the business", validators=[Required()])
    submit = SubmitField()

class ReturnForm(FlaskForm):
    business_name = StringField("Please enter the name of a business.", validators=[Required()])
    goback = StringField("Would you go back/continue doing business? (Yes/No).",validators=[Required()])
    reason = StringField("Explain why you would or would not continue using/going to this business.", validators=[Required()])
    submit = SubmitField()

    def validate_reason(self, field):
        if len(field.data) <2:
            raise ValidationError("Please enter valid information!")




#######################
###### VIEW FXNS ######
#######################
#url and api key to access yelp
baseurl= 'https://api.yelp.com/v3/businesses/search?term='
api_key = 'jNEm-Q_rzJM4Op8MG3WHQXcoQgDZqKzgTFPsuBFKD-zRh0FF3QhqkzJnxqRqYZkjA-JuBHYlEwWqT-4VArO4Zxjbvbffls3OR6Px-BAQLlH5fCu6HJZLfN6qUuelWnYx'


@app.route('/', methods=['GET', 'POST'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        business = form.business.data
        review = form.review.data
        newname = Name(name= name)
        db.session.add(newname)
        db.session.commit()
        
        #check if business and review are in table
        business_rev = Review.query.filter_by(review = review).first()
        if business_rev:
            new_business = Review.query.filter_by(review = review)
        else:
            new_business = Review(review=review)
            db.session.add(new_business)
            db.session.commit()
        return redirect(url_for('business'))
    return render_template('base.html',form=form)
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('base.html', form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)



@app.route('/business', methods=['GET', 'POST'])
def business():
    form = BusinessForm()
    baseurl= 'https://api.yelp.com/v3/businesses/search'
    api_key = 'jNEm-Q_rzJM4Op8MG3WHQXcoQgDZqKzgTFPsuBFKD-zRh0FF3QhqkzJnxqRqYZkjA-JuBHYlEwWqT-4VArO4Zxjbvbffls3OR6Px-BAQLlH5fCu6HJZLfN6qUuelWnYx'
    if form.validate_on_submit():
        business_name = form.business_name.data
        location = form.location.data
        yelp_url = baseurl + business_name + "&limit=1&location=" + location
        yelp_api = requests.get(yelp_url, headers = {'Authorization': 'Bearer' + api_key, 'token_type': 'Bearer'})
        yelp_json = json.loads(yelp_api.text)
        for x in yelp_json['business']:
            business_name = x['name']
            location = x['location.address1']
            price = x['price']
            rating = x['rating']
            y_reviews = Business.query.filter_by(business_name= business_name, location=location,price=price, rating=rating).first()
            prev_r = Review.query.filter_by(business_id= y_reviews.id)
            if prev_r:
                new_id= prev_r
            else:
                new_id = Review(business_id= y_reviews.id)
                db.session.add(new_id)
                db.session.commit()
        if y_reviews:
            flash('Review already entered!')
        else:
            y_reviews = Business.query.filter_by(business_name= business_name, location=location,price=price, rating=rating)
            db.session.add(y_reviews)
            db.session.commit()
        return redirect(url_for('business'))
    return render_template('business.html', form=form)

@app.route('/returntobusiness', methods=['GET', 'POST'])
def return_form():
    form = ReturnForm(request.form)
    if request.args:
        business_name = request.args.get('business_name')
        goback = request.args.get('goback')
        reason = request.args.get('reason')
        r_data = Reasons(business_name= business_name, goback=goback, reason=reason)
        db.session.add(r_data)
        db.session.commit()
    return render_template('returntobusiness.html', form= form)
    return redirect(url_for('business'))

@app.route('/all_returns')
def all_returns():
    returns = Returns.query.all()
    return render_template("all_returns.html", returns=returns)



@app.route('/all_businesses')
def all_businesses():
    businesses = Business.query.all()
    return render_template('all_businesses.html', businesses_info= business)







## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!

if __name__=='__main__':
    db.create_all()
    manager.run()











