from functools import wraps

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import db
from app.auth.routes import admin_required
from app.models import Activity, Game, Team, TeamActivity, User, Input
from app.main import bp
from app.main.forms import TeamAssign, UserForm, GameAssignForm, GameCreateForm, GamePlayForm, GameUserForm

INTEREST_RATE_PER_MONTH = 0.042
RENT_PER_MONTH = 900


def _commit_object_to_db(model, **kwargs):
    object_ = model(**kwargs)
    db.session.add(object_)
    db.session.commit()
    return object_


def get_or_create(session, model, **kwargs):
    """
    session, model, **kwargs
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def _delete_object_from_db(model, **kwargs):
    object_ = model.query.filter_by(**kwargs).first()
    if not object_:
        raise ValueError(f'Object not found, {kwargs}')
    db.session.delete(object_)
    db.session.commit()
    return object_


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
        initial_team_input = Input(id=f'{team.id}_{game_.current_day}', team_id=team.id, active_at_day=game_.current_day)
        db.session.add(game_)
        db.session.add(initial_team_input)
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
            _calculate_next_period(game_)
            game_.increase_current_day(10)
        elif form.increase_period.data == 'decrease':
            game_.decrease_current_day(10)
        db.session.add(game_)
        db.session.commit()
    return render_template('game.html', form=form, game=game_)


def _calculate_next_period(game_):
    for team_ in game_.teams:
        current_period_input = get_or_create(db.session, Input, id=f'{team_.id}_{game_.current_day}',
                                             team_id=team_.id, active_at_day=game_.current_day)
        import pdb;
        pdb.set_trace()
        for act in current_period_input.activities:
            pass


# player
@bp.route('/play', methods=['GET', 'POST'])
@login_required
def play():
    user_ = current_user
    team_ = current_team()
    game_ = current_game()
    form = GameUserForm()
    input_ = get_or_create(db.session, Input, id=f'{team_.id}_{game_.current_day}',
                           team_id=team_.id, active_at_day=game_.current_day)

    _none_option = [('none_of_the_above', '-')]
    all_activities = Activity.query.all()
    activities_to_dict = {k: v for k, v in [(a.id, a.title) for a in all_activities]}
    activities_object_map = {k: v for k, v in [(a.id, a) for a in all_activities]}

    to_be_started = TeamActivity.query.filter_by(team=team_.id, started_on_day=game_.current_day).all()
    finished = _get_finished_activities(team_, game_)
    in_progress = [ta for ta in TeamActivity.query.filter_by(team=team_.id).all()
                   if ta.started_on_day < game_.current_day]

    unavailable_activities = [a.activity_id for a in finished + in_progress + to_be_started]
    available_activities = _none_option + [(a.id, a.title) for a in Activity.query.all()
                                           if a.id not in unavailable_activities]
    form.add_activity.choices = available_activities
    form.remove_activity.choices = _none_option + [(a.id, activities_to_dict[a.activity_id])
                                                   for a in to_be_started]

    if not (user_.is_cashier or user_.is_manager):
        del form.add_activity
        del form.remove_activity
        del form.apply_for_credit
        del form.submit

    if form.validate_on_submit():
        redirect_ = redirect(url_for('main.play', form=form, team=team_, game=game_,
                                     started=to_be_started, finished=finished, in_progress=in_progress))

        credit = form.apply_for_credit.data
        if not validate_and_update_credit(credit, input_):
            return redirect_

        if (form.add_activity.data != 'none_of_the_above'
                and form.add_activity.data not in unavailable_activities):
            to_add = _commit_object_to_db(TeamActivity, activity_id=form.add_activity.data,
                                          team=team_.id,
                                          input_id=f'{team_.id}_{game_.current_day}',
                                          initiated_on_day=game_.current_day)
            flash(f'{activities_to_dict[to_add.activity_id]} added')
            if not form.remove_activity.data != 'none_of_the_above':
                return redirect_
        if form.remove_activity.data != 'none_of_the_above':
            to_remove = _delete_object_from_db(TeamActivity, id=form.remove_activity.data)
            flash(f'{activities_to_dict[to_remove.activity_id]} removed')
            return redirect_

    return render_template('play.html', form=form, team=team_, game=game_,
                           credit_to_take=input_.credit,
                           started=[activities_object_map[a.activity_id] for a in to_be_started],
                           finished=[activities_object_map[a.activity_id] for a in finished],
                           in_progress=[activities_object_map[a.activity_id] for a in in_progress])


def validate_and_update_credit(credit, input_):
    if not credit:
        return True

    if credit > 0:
        if not credit % 300 == 0:
            flash(f'Credit should be increment of 300')
            return False
        if credit > 10000:
            flash(f'Maximum size of credit is 9900')
            return False

    input_.credit = credit
    db.session.add(input_)
    db.session.commit()
    return True



def _get_finished_activities(team_, game_):
    result = []
    for ta in TeamActivity.query.filter_by(team=team_.id).all():
        activity = Activity.query.filter_by(id=ta.activity_id).first()
        if game_.current_day - ta.started_on_day >= activity.days_needed:
            result.append(ta)
    return result
