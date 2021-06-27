from functools import wraps

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import db
from app.auth.routes import admin_required
from app.models import User, Team
from app.main import bp
from app.main.forms import TeamAssign, UserForm


@bp.route('/')
@bp.route('/index')
def index():
    return render_template('base.html')


@bp.route('/teams')
@login_required
@admin_required
def teams():
    teams = Team.query.filter_by(is_active=True).all()
    return render_template('teams.html', teams=teams)


@bp.route('/teams/<team_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def team(team_id):
    current_team = Team.query.filter_by(id=team_id).first()
    unnasigned_users = User.query.filter_by(team_id=None, is_admin=False).all()
    form = TeamAssign(obj=current_team)
    form.user.choices = [u.username for u in unnasigned_users]
    if form.validate_on_submit():
        added_user_username = form.user.data
        # depends on value dipslayed on form
        user = User.query.filter_by(username=added_user_username).first()
        user.team_id = current_team.id
        db.session.add(user)
        db.session.commit()
        flash(f'Successfully updated scenario')
    return render_template('team.html', form=form, team=current_team)


@bp.route('/users/<user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user(user_id):
    current_user = User.query.filter_by(id=user_id).first()
    teams = Team.query.filter_by(is_active=True).all()
    form = UserForm(obj=current_user)
    form.team_id.choices = [(t.id, f'Team {t.id}, {t.display_name}') for t in teams]
    if form.validate_on_submit():
        form.populate_obj(current_user)
        db.session.add(current_user)
        db.session.commit()
        flash(f'Successfully updated {current_user} id:{current_user.id}.')
        return redirect(url_for('main.users'))
    return render_template('user.html', form=form, user=current_user)


@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.filter_by(is_active=True, is_admin=False).all()
    return render_template('users.html', users=users)
