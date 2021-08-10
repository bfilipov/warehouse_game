from functools import wraps

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import db
from app.auth.routes import admin_required
from app.models import User, Team, Game
from app.main import bp
from app.main.forms import TeamAssign, UserForm, GameAssignForm, GameCreateForm, GamePlayForm, GameUserForm


def current_team():
    current_team_ = Team.query.filter_by(id=current_user.team_id).first()
    return current_team_


def current_game():
    current_team_ = current_team()
    return Game.query.filter_by(id=current_team_.game_id).first()


@bp.route('/')
@bp.route('/index')
def index():
    return render_template('base.html')


@bp.route('/teams')
@login_required
@admin_required
def teams():
    teams_ = Team.query.filter_by(is_active=True).all()
    return render_template('teams.html', teams=teams_)


@bp.route('/teams/<team_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def team(team_id):
    current_team_ = Team.query.filter_by(id=team_id).first()
    unnasigned_users = User.query.filter_by(team_id=None, is_admin=False).all()
    form = TeamAssign(obj=current_team_)
    form.user.choices = [u.username for u in unnasigned_users]
    if form.validate_on_submit():
        form.populate_obj(current_team_)
        db.session.add(current_team_)
        db.session.commit()
        if form.user.data:
            added_user_username = form.user.data
            # depends on value dipslayed on form
            user_ = User.query.filter_by(username=added_user_username).first()
            user_.team_id = current_team_.id
            db.session.add(user_)
            db.session.commit()
        flash(f'Successfully updated team.')
    return render_template('team.html', form=form, team=current_team_)


@bp.route('/users/<user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user(user_id):
    current_user_ = User.query.filter_by(id=user_id).first()
    teams_ = Team.query.filter_by(is_active=True).all()
    form = UserForm(obj=current_user_)
    form.team_id.choices = [(t.id, f'Team {t.id}, {t.display_name}') for t in teams_]
    if form.validate_on_submit():
        form.populate_obj(current_user_)
        db.session.add(current_user_)
        db.session.commit()
        flash(f'Successfully updated {current_user_} id:{current_user_.id}.')
        return redirect(url_for('main.users'))
    return render_template('user.html', form=form, user=current_user_)


@bp.route('/users')
@login_required
@admin_required
def users():
    users_ = User.query.filter_by(is_active=True, is_admin=False).all()
    return render_template('users.html', users=users_)


@bp.route('/games', methods=['GET', 'POST'])
@login_required
@admin_required
def games():
    games_ = Game.query.filter_by(is_active=True).all()
    form = GameCreateForm()
    if form.validate_on_submit():
        game_ = Game()
        db.session.add(game_)
        db.session.commit()
        flash(_('New game created.'))
        return redirect(url_for('main.games'))
    return render_template('games.html', form=form, games=games_)


@bp.route('/games/<game_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def game_edit(game_id):
    game_ = Game.query.filter_by(id=game_id).first()
    form = GameAssignForm(obj=game_)
    unassigned_teams = Team.query.filter_by(game_id=None, is_active=True).all()
    form.team.choices = [(t.id, f'Team {t.id}, {t.display_name}') for t in unassigned_teams]
    if form.validate_on_submit():
        added_team = Team.query.filter_by(id=form.team.data).first()
        game_.teams.append(added_team)
        db.session.add(game_)
        db.session.commit()
        flash(f'Successfully added team.')
        return redirect(url_for('main.game', game_id=game_.id))
    return render_template('game_edit.html', form=form, game=game_)


@bp.route('/games/<game_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def game(game_id):
    game_ = Game.query.filter_by(id=game_id).first()
    form = GamePlayForm(obj=game_)
    if form.validate_on_submit():
        if form.increase_period.data == 'increase':
            game_.increase_current_day(10)
        elif form.increase_period.data == 'decrease':
            game_.decrease_current_day(10)
        db.session.add(game_)
        db.session.commit()
    return render_template('game.html', form=form, game=game_)


# player
@bp.route('/play', methods=['GET', 'POST'])
@login_required
def play():
    team_ = current_team()
    game_ = current_game()
    form = GameUserForm()
    return render_template('play.html', form=form, team=team_, game=game_)
