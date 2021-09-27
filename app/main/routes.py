from functools import wraps

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import db
from app.auth.routes import admin_required
from app.models import Activity, ActivityRequirement, Game, Team, TeamActivity, User, Input
from app.main import bp
from app.main.forms import TeamAssign, UserForm, GameAssignForm, GameCreateForm, GamePlayForm, GameUserForm, TeamForm

INTEREST_RATE_PER_MONTH = 0.042
RENT_PER_MONTH = 900
MAX_DAY = 999999999
NONE_OPTION = [('none_of_the_above', '-')]
PERIOD_INCREMENT_IN_DAYS = 10
NOT_ENOUGH_FUNDS_PENALTY = 60
STARTING_FUNDS = 2100


def _commit_object_to_db(model, **kwargs):
    object_ = model(**kwargs)
    db.session.add(object_)
    db.session.commit()
    return object_


def get_or_create(model, **kwargs):
    """
    session, model, **kwargs
    """
    instance = db.session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
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


@bp.route('/teams', methods=['GET', 'POST'])
@login_required
@admin_required
def teams():
    teams_ = Team.query.filter_by(is_active=True).all()
    form = TeamForm()
    if form.validate_on_submit():
        new_team = Team()
        form.populate_obj(new_team)
        db.session.add(new_team)
        db.session.commit()
        return redirect(url_for('main.teams', teams=teams_, form=form))
    return render_template('teams.html', teams=teams_, form=form)


@bp.route('/teams/<team_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def team(team_id):
    current_team_ = Team.query.filter_by(id=team_id).first()
    unnasigned_users = User.query.filter_by(team_id=None, is_admin=False).all()
    form = TeamAssign(obj=current_team_)
    form.add_user.choices = NONE_OPTION + [(u.id, u.username) for u in unnasigned_users]
    form.remove_user.choices = NONE_OPTION + [(u.id, u.username) for u in current_team_.users]

    if form.validate_on_submit():
        # currently ised for is_active checkbox
        form.populate_obj(current_team_)
        db.session.add(current_team_)
        db.session.commit()
        # currently ised for is_active checkbox

        if form.add_user.data not in [None, NONE_OPTION[0][0]]:
            change_object_reference_id(User, form.add_user.data, 'team_id', current_team_.id)

        if form.remove_user.data not in [None, NONE_OPTION[0][0]]:
            change_object_reference_id(User, form.remove_user.data, 'team_id', None)

        flash(f'Successfully updated team.')
        return redirect(url_for('main.team', team_id=current_team_.id))
    return render_template('team.html', form=form, team=current_team_)


def change_user_teamid(user_id, team_id):
    # depends on value dipslayed on form
    user_ = User.query.filter_by(id=user_id).first()
    user_.team_id = team_id
    db.session.add(user_)
    db.session.commit()


def change_object_reference_id(object_model, object_id,
                               object_reference_id, object_reference_id_value):
    # generalize the above function
    obj = object_model.query.filter_by(id=object_id).first()
    setattr(obj, object_reference_id, object_reference_id_value)
    db.session.add(obj)
    db.session.commit()


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
    form = None
    games_ = Game.query.filter_by(is_active=True).all()
    if current_user.is_superadmin:
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
    assigned_teams = Team.query.filter_by(game_id=game_id, is_active=True).all()
    form.add_team.choices = NONE_OPTION + [(t.id, f'Team {t.id}, {t.display_name}') for t in unassigned_teams]
    form.remove_team.choices = NONE_OPTION + [(t.id, f'Team {t.id}, {t.display_name}') for t in assigned_teams]
    if form.validate_on_submit():

        if form.add_team.data not in [None, NONE_OPTION[0][0]]:
            change_object_reference_id(Team, form.add_team.data, 'game_id', game_.id)
            initial_team_input = get_or_create(Input,
                                               id=f'{game_.id}_{form.add_team.data}_{game_.current_day}',
                                               team_id=form.add_team.data,
                                               game_id=game_.id,
                                               active_at_day=game_.current_day)
            db.session.add(game_)
            db.session.add(initial_team_input)
            db.session.commit()

        if form.remove_team.data not in [None, NONE_OPTION[0][0]]:
            change_object_reference_id(Team, form.remove_team.data, 'game_id', None)

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
            if game_.current_day < MAX_DAY:
                _calculate_next_period(game_)
                game_.increase_current_day(PERIOD_INCREMENT_IN_DAYS)
            else:
                flash('Max day reached.')
        elif form.increase_period.data == 'decrease':
            game_.decrease_current_day(PERIOD_INCREMENT_IN_DAYS)
        db.session.add(game_)
        db.session.commit()
    return render_template('game.html', form=form, game=game_)


def get_current_period_input(team_, game_):
    current_period_input = get_or_create(Input,
                                         id=f'{game_.id}_{team_.id}_{game_.current_day}',
                                         team_id=team_.id,
                                         game_id=game_.id,
                                         active_at_day=game_.current_day)
    if game_.current_day == 1:
        current_period_input.credit_taken = STARTING_FUNDS
        current_period_input.money_at_start_of_period = STARTING_FUNDS
    else:
        previous_period_input = get_or_create(Input,
                                              id=f'{game_.id}_{team_.id}_{game_.current_day-PERIOD_INCREMENT_IN_DAYS}',
                                              team_id=team_.id,
                                              game_id=game_.id,
                                              active_at_day=game_.current_day-PERIOD_INCREMENT_IN_DAYS)
        current_period_input.credit_taken = previous_period_input.credit_taken + previous_period_input.credit_to_take
        current_period_input.money_at_start_of_period = (previous_period_input.money_at_end_of_period
                                                         + previous_period_input.credit_to_take)
    return current_period_input


def _calculate_next_period(game_):
    for team_ in game_.teams:

        current_period_input = get_current_period_input(team_, game_)

        next_period_day = game_.current_day + PERIOD_INCREMENT_IN_DAYS
        next_period_input = get_or_create(Input,
                                          id=f'{game_.id}_{team_.id}_{next_period_day}',
                                          team_id=team_.id,
                                          game_id=game_.id,
                                          active_at_day=next_period_day)
        penalty = 0
        available_money = current_period_input.money_at_start_of_period
        for team_act in current_period_input.activities:
            act = Activity.query.filter_by(id=team_act.activity_id).first()
            if start_if_is_activity_eligible(act, team_act, available_money, team_, game_):
                available_money -= act.cost
            else:
                # if no funds available for current round, move activity for next round
                team_act.input_id = next_period_input.id
                team_act.penalty_from_previous_period = NOT_ENOUGH_FUNDS_PENALTY

        current_period_input.money_at_end_of_period = available_money + current_period_input.credit_to_take
        db.session.add(current_period_input)
        db.session.commit()


def start_if_is_activity_eligible(act, team_act, available_money, team_, game_):
    required_acts = ActivityRequirement.query.filter_by(activity_id=act.id).all()
    finished_acts = [ta.activity_id for ta in _get_finished_activities(team_, game_)]
    for a in required_acts:
        if a.requirement_id not in finished_acts:
            return False
    if act.cost >= available_money:
        return False

    team_act.penalty_from_previous_period = 0
    team_act.started_on_day = game_.current_day
    team_act.finished_on_day = game_.current_day + act.days_needed
    return True


# player
@bp.route('/play', methods=['GET', 'POST'])
@login_required
def play():
    state = {}
    user_ = current_user
    try:
        team_ = current_team()
        game_ = current_game()
    except AttributeError as e:
        flash('Not yet started')
        return redirect('/')

    form = GameUserForm()
    input_ = get_current_period_input(team_, game_)

    all_activities = Activity.query.all()
    activities_to_dict = {k: v for k, v in [(a.id, f'{a.title} Ценa:{a.cost}') for a in all_activities]}
    state['activities_object_map'] = {k: v for k, v in [(a.id, a) for a in all_activities]}

    to_be_started = TeamActivity.query.filter_by(game=game_.id, team=team_.id, started_on_day=MAX_DAY).all() + \
                    TeamActivity.query.filter_by(game=game_.id, team=team_.id, started_on_day=game_.current_day).all()
    finished = _get_finished_activities(team_, game_)
    in_progress = [ta for ta in TeamActivity.query.filter_by(game=game_.id, team=team_.id).all()
                   if ta.started_on_day < game_.current_day and ta not in finished]

    unavailable_activities = [a.activity_id for a in finished + in_progress + to_be_started]
    available_activities = NONE_OPTION + [(a.id, f'{a.title} Ценa:{a.cost}') for a in Activity.query.all()
                                          if a.id not in unavailable_activities]

    form.add_activity.choices = available_activities
    form.remove_activity.choices = NONE_OPTION + [(a.id, activities_to_dict[a.activity_id])
                                                  for a in to_be_started]

    if not (user_.is_cashier or user_.is_manager):
        del form.add_activity
        del form.remove_activity
        del form.apply_for_credit
        del form.submit

    state['team'] = team_
    state['game'] = game_
    state['money_at_start_of_period'] = input_.money_at_start_of_period
    state['credit_taken'] = input_.credit_taken
    state['started'] = to_be_started
    state['finished'] = sorted(finished, key=lambda ta: ta.finished_on_day)
    state['in_progress'] = in_progress

    if form.validate_on_submit():
        should_redirect = False
        redirect_ = redirect(url_for('main.play', form=form, state=state))

        # update credit
        credit_to_take = form.apply_for_credit.data
        if not validate_and_update_credit(credit_to_take, input_):
            should_redirect = True

        # add activity
        if (form.add_activity.data != NONE_OPTION[0][0]
                and form.add_activity.data not in unavailable_activities
                and form.add_activity.data not in [i.activity_id for i in input_.activities]):
            to_add = get_or_create(TeamActivity,
                                   id=f'{game_.id}_{team_.id}_{form.add_activity.data}')
            to_add.activity_id = form.add_activity.data
            to_add.team = team_.id
            to_add.game = game_.id
            to_add.started_on_day = MAX_DAY
            to_add.finished_on_day = MAX_DAY
            to_add.initiated_on_day = game_.current_day
            to_add.input_id = f'{game_.id}_{team_.id}_{game_.current_day}'
            commit_to_db(to_add)

            flash(f'{activities_to_dict[to_add.activity_id]} added')
            if not form.remove_activity.data != 'none_of_the_above':
                should_redirect = True

        # remove activity
        if form.remove_activity.data != 'none_of_the_above':
            to_remove = _reset_team_activity(id=form.remove_activity.data)
            flash(f'{activities_to_dict[to_remove.activity_id]} removed')
            should_redirect = True

        if should_redirect:
            return redirect_

    state['credit_to_take'] = input_.credit_to_take
    state['started'] = to_be_started
    state['finished'] = sorted(finished, key=lambda ta: ta.finished_on_day)
    state['in_progress'] = in_progress

    return render_template('play.html', form=form, state=state)


def _reset_team_activity(id):
    activity = TeamActivity.query.filter_by(id=id).first()
    activity.started_on_day = None
    activity.finished_on_day = MAX_DAY
    activity.initiated_on_day = None
    db.session.add(activity)
    db.session.commit()
    return activity


def commit_to_db(object):
    db.session.add(object)
    db.session.commit()


def validate_and_update_credit(credit, input_):
    # should allow 0
    if credit is None:
        return True

    if credit > 0:
        if not credit % 300 == 0:
            flash(f'Credit should be increment of 300')
            return False
        if credit > 10000:
            flash(f'Maximum size of credit is 9900')
            return False

    input_.credit_to_take = credit
    db.session.add(input_)
    db.session.commit()
    return True


def _get_finished_activities(team_, game_):
    result = []
    for ta in TeamActivity.query.filter_by(team=team_.id, game=game_.id).all():
        if game_.current_day >= ta.finished_on_day:
            result.append(ta)
    return result
