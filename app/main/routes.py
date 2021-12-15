import io
import csv
from functools import wraps

from flask import flash, redirect, render_template, url_for, make_response
from flask_babel import _
from flask_login import current_user, login_required

from app import db
from app.auth.routes import admin_required
from app.models import Activity, ActivityRequirement, Game, Team, TeamActivity, \
    User, Input, InputHistory, Penalty
from app.main import bp
from app.main.forms import TeamAssign, UserForm, GameAssignForm, GameCreateForm, \
    GamePlayForm, GameUserForm, TeamForm

INTEREST_RATE_PER_MONTH = 0.042
RENT_PER_MONTH = 900
MAX_DAY = 999999999
NONE_OPTION = [('none_of_the_above', '-')]
PERIOD_INCREMENT_IN_DAYS = 10
DAYS_IN_GAME_MONTH = 30
NOT_ENOUGH_FUNDS_PENALTY = 60
STARTING_FUNDS = 2100
PROFIT_PER_DAY = 75


def no_http_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, private, max-age=0')
        return response
    return no_cache_view


def commit_to_db(object_):
    db.session.add(object_)
    db.session.commit()


def commit_object_to_db(model, **kwargs):
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


@bp.route('/reports', methods=['GET'])
@login_required
@admin_required
def reports():
    games_ = Game.query.filter_by(is_active=True).all()
    return render_template('reports.html',  games=games_)


@bp.route('/reports/<game_id>', methods=['GET'])
@login_required
@admin_required
def report(game_id):
    game_ = Game.query.filter_by(id=game_id).first()
    activities = Activity.query.all()
    return render_template('report.html',  game=game_, activities=activities)

@bp.route('/game_status/<game_id>', methods=['GET'])
@login_required
@admin_required
def game_status(game_id):
    game_ = Game.query.filter_by(id=game_id).first()
    teams_stub = []

    for team_ in game_.teams.all():
        current_input = Input.query.filter_by(team_id=team_.id, active_at_day=game_.current_day).first()
        if current_input:
            t = {}
            t.update({'id': team_.id})
            t.update({'day': game_.current_day})
            t.update({'current_money': current_input.money_at_start_of_period})
            t.update({'credit_taken': current_input.credit_taken})
            t.update({'finished': [ta.activity_id for ta in _get_finished_activities(team_, game_)]})
            t.update({'total_interest_cost': sum([i.interest_cost
                                                  for i in Input.query.filter_by(team_id=team_.id).all()])})
            t.update({'total_penalty_cost': sum([i.total_penalty_cost
                                                 for i in Input.query.filter_by(team_id=team_.id).all()])})
            t.update({'total_rent_cost': sum([i.rent_cost
                                              for i in Input.query.filter_by(team_id=team_.id).all()])})
            teams_stub.append(t)

    return render_template('main_report.html',  teams=teams_stub)


@bp.route('/games/<game_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def game_edit(game_id):
    game_ = Game.query.filter_by(id=game_id).first()
    form = GameAssignForm(obj=game_)
    unassigned_teams = Team.query.filter_by(game_id=None, is_active=True).all()
    assigned_teams = Team.query.filter_by(game_id=game_id, is_active=True).all()
    form.add_team.choices = NONE_OPTION + [
        (t.id, f'Team {t.id}, {t.display_name}') for t in unassigned_teams]
    form.remove_team.choices = NONE_OPTION + [
        (t.id, f'Team {t.id}, {t.display_name}') for t in assigned_teams]
    if form.validate_on_submit():
        if form.add_team.data not in [None, NONE_OPTION[0][0]]:
            change_object_reference_id(Team, form.add_team.data, 'game_id', game_.id)
            initial_team_input = get_or_create(Input,
                                               id=f'{game_.id}_{form.add_team.data}_{game_.current_day}')
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
                commit_to_db(game_)
            else:
                flash('Max day reached.')
        elif form.increase_period.data == 'decrease':
            game_.decrease_current_day(PERIOD_INCREMENT_IN_DAYS)
            commit_to_db(game_)
            _update_team_inputs(game_)
            _reset_current_input(game_)
    return render_template('game.html', form=form, game=game_)


def _reset_current_input(game_):
    for team_ in game_.teams:
        current_input = Input.query.filter_by(team_id=team_.id, active_at_day=game_.current_day).first()
        current_input.credit_to_take = 0
        for ta in current_input.activities.all():
            if ta.initiated_on_day == game_.current_day:
                db.session.delete(ta)
                db.session.commit()
        commit_to_db(current_input)


def _update_team_inputs(game_):
    for team_ in game_.teams:
        for input_ in team_.inputs:
            if game_.current_day < input_.active_at_day:
                for team_act in input_.activities:
                    db.session.delete(team_act)
                    db.session.commit()
                db.session.delete(input_)
                db.session.commit()


def get_current_period_input(team_, game_):
    current_period_input = get_or_create(Input,
                                         id=f'{game_.id}_{team_.id}_{game_.current_day}')
    current_period_input.team_id = team_.id
    current_period_input.game_id = game_.id
    current_period_input.active_at_day = game_.current_day
    commit_to_db(current_period_input)

    if game_.current_day == 1:
        current_period_input.credit_taken = STARTING_FUNDS
        current_period_input.money_at_start_of_period = STARTING_FUNDS
    commit_to_db(current_period_input)

    return current_period_input


def _calculate_next_period(game_):
    all_activities = Activity.query.all()
    for team_ in game_.teams:
        current_period_input = get_current_period_input(team_, game_)
        next_period_day = game_.current_day + PERIOD_INCREMENT_IN_DAYS
        next_period_input = get_or_create(Input,
                                          id=f'{game_.id}_{team_.id}_{next_period_day}',
                                          team_id=team_.id,
                                          game_id=game_.id,
                                          active_at_day=next_period_day)

        _, _, finished = get_team_activities(game_, team_)
        completed_all = set([i.activity_id for i in finished]) == set([i.id for i in all_activities])

        available_money = current_period_input.money_at_start_of_period
        for team_act in current_period_input.activities:
            act = Activity.query.filter_by(id=team_act.activity_id).first()
            if start_if_is_activity_eligible(act, team_act, available_money, team_, game_):
                available_money -= act.cost
            else:
                # if no funds available for current round, move activity for next round
                # # should we activate team_activity from previous period for next period?
                # lets try_not_to
                # team_act.input_id = next_period_input.id
                # team_act.initiated_on_day = next_period_input.active_at_day
                # commit_to_db(team_act)
                penalty = Penalty(input_id=next_period_input.id, activity_id=act.id)
                commit_to_db(penalty)

        _update_funds_for_current_and_next_period(current_period_input, next_period_input,
                                                  available_money, completed_all)


def _update_funds_for_current_and_next_period(current_period_input, next_period_input,
                                              available_money, completed_all):
    profit = PROFIT_PER_DAY * PERIOD_INCREMENT_IN_DAYS if completed_all else 0
    next_period_penalties = Penalty.query.filter_by(input_id=next_period_input.id).all()
    total_penalty = sum([i.fine for i in next_period_penalties])
    next_period_input.total_penalty_cost = total_penalty
    next_period_input.credit_taken = (current_period_input.credit_taken
                                      + current_period_input.credit_to_take
                                      - profit)
    next_period_input.interest_cost = current_period_input.credit_taken * (
            INTEREST_RATE_PER_MONTH * (PERIOD_INCREMENT_IN_DAYS / DAYS_IN_GAME_MONTH))
    next_period_input.rent_cost = RENT_PER_MONTH if (
            (next_period_input.active_at_day-1) % DAYS_IN_GAME_MONTH == 0) else 0
    next_period_input.money_at_start_of_period = (available_money + current_period_input.credit_to_take
                                                  + profit
                                                  - next_period_input.total_penalty_cost
                                                  - next_period_input.interest_cost
                                                  - next_period_input.rent_cost)
    current_period_input.money_at_end_of_period = next_period_input.money_at_start_of_period
    commit_to_db(current_period_input)
    commit_to_db(next_period_input)


def start_if_is_activity_eligible(act, team_act, available_money, team_, game_):
    required_acts = ActivityRequirement.query.filter_by(activity_id=act.id).all()
    finished_acts = [ta.activity_id for ta in _get_finished_activities(team_, game_)]
    for a in required_acts:
        if a.requirement_id not in finished_acts:
            return False
    if act.cost > available_money:
        return False

    team_act.started_on_day = game_.current_day
    team_act.finished_on_day = game_.current_day + act.days_needed
    return True


def get_team_activities(game_, team_):
    to_be_started = TeamActivity.query.filter_by(game=game_.id, team_id=team_.id,
                                                 initiated_on_day=game_.current_day).all()
    finished = _get_finished_activities(team_, game_)
    in_progress = []
    for ta in TeamActivity.query.filter_by(game=game_.id, team_id=team_.id).all():
        if ta.started_on_day < game_.current_day and ta not in finished:
            in_progress.append(ta)
    return to_be_started, in_progress, finished


# player
@bp.route('/play', methods=['GET'])
@login_required
@no_http_cache
def play_get():
    state = {}
    try:
        team_ = current_team()
        game_ = current_game()
    except AttributeError as e:
        flash('Not yet started')
        return redirect('/')

    form = GameUserForm()
    user_ = current_user
    input_ = get_current_period_input(team_, game_)

    all_activities = Activity.query.all()
    state['activities_object_map'] = {k: v for k, v in [(a.id, a) for a in all_activities]}

    to_be_started, in_progress, finished = get_team_activities(game_, team_)

    state['team'] = team_
    state['game'] = game_
    state['money_at_start_of_period'] = input_.money_at_start_of_period
    state['rent_cost'] = input_.rent_cost
    state['credit_taken'] = input_.credit_taken
    state['credit_to_take'] = input_.credit_to_take
    state['interest_cost'] = input_.interest_cost

    state['finished'] = sorted(finished, key=lambda ta: ta.finished_on_day)
    state['in_progress'] = in_progress
    state['started'] = to_be_started

    penalties = Penalty.query.filter_by(input_id=input_.id).all()
    state['penalties'] = penalties
    state['total_penalties_cost'] = sum([i.fine for i in penalties])

    all_activities = Activity.query.all()

    activities_to_dict = {k: v for k, v in [(a.id, f'{a.title} Ценa:{a.cost}') for a in all_activities]}
    state['activities_object_map'] = {k: v for k, v in [(a.id, a) for a in all_activities]}

    unavailable_activities = [a.activity_id for a in finished + in_progress + to_be_started]
    available_activities = NONE_OPTION + [(a.id, f'{a.title} Ценa:{a.cost}') for a in Activity.query.all()
                                          if a.id not in unavailable_activities]

    form.add_activity.choices = available_activities
    form.remove_activity.choices = NONE_OPTION + [(a.id, activities_to_dict[a.activity_id])
                                                  for a in to_be_started]

    if not user_.is_manager:
        del form.add_activity
        del form.remove_activity
        del form.apply_for_credit
        del form.submit

    return render_template('play.html', form=form, state=state)


@bp.route('/play', methods=['POST'])
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

    to_be_started, in_progress, finished = get_team_activities(game_, team_)

    all_activities = Activity.query.all()
    activities_to_dict = {k: v for k, v in [(a.id, f'{a.title} Ценa:{a.cost}') for a in all_activities]}
    state['activities_object_map'] = {k: v for k, v in [(a.id, a) for a in all_activities]}

    unavailable_activities = [a.activity_id for a in finished + in_progress + to_be_started]
    available_activities = NONE_OPTION + [(a.id, f'{a.title} Ценa:{a.cost}') for a in Activity.query.all()
                                          if a.id not in unavailable_activities]

    form.add_activity.choices = available_activities
    form.remove_activity.choices = NONE_OPTION + [(a.id, activities_to_dict[a.activity_id])
                                                  for a in to_be_started]

    if form.validate_on_submit():
        input_history = InputHistory(team_id=team_.id, game_id=game_.id, current_day=game_.current_day,
                                     activity_to_add=None, activity_to_remove=None, credit_to_take=0)
        # update credit
        credit_to_take = form.apply_for_credit.data
        input_history.credit_to_take = form.apply_for_credit.data
        validate_and_update_credit(credit_to_take, input_)

        # add activity
        if (form.add_activity.data != NONE_OPTION[0][0]
                and form.add_activity.data not in unavailable_activities):
            to_add = get_or_create(TeamActivity,
                                   id=f'{game_.id}_{team_.id}_{form.add_activity.data}')
            set_team_activity(to_add, team_, game_)
            input_history.activity_to_add = form.add_activity.data
            flash(f'{activities_to_dict[to_add.activity_id]} added')

        # remove activity
        if form.remove_activity.data != 'none_of_the_above':
            _reset_team_activity(id_=form.remove_activity.data)
            input_history.activity_to_remove = form.remove_activity.data.split('_')[-1]

        commit_to_db(input_history)
    return redirect(url_for('main.play_get'))


@bp.route('/results', methods=['GET'])
@login_required
def team_results():
    try:
        team_ = current_team()
    except AttributeError:
        flash('Not yet started')
    game_stub = {'teams': [team_]}
    activities = Activity.query.all()
    return render_template('report.html', game=game_stub, activities=activities)


@bp.route('/admin/download_results/<game_id>')
@login_required
@admin_required
def admin_download_results(game_id):
    """
    View download totals for all games """
    game_ = Game.query.filter_by(id=game_id).first()
    columns = {"team_id": "Team id", "active_at_day": "Day",
               "money_at_start_of_period": "Money start",
               "money_at_end_of_period": "Money end", "credit_taken": "Credit taken",
               "credit_to_take": "Credit to take", "interest_cost": "Interest costs",
               "total_penalty_cost": "Total penalty cost", "rent_cost": "Rent cost"}

    activities = ["Activity A", "Activity B",
                  "Activity C", "Activity D",
                  "Activity E", "Activity F",
                  "Activity G", "Activity H",
                  "Activity I", "Activity J",
                  "Activity K}", "Activity L"]

    if not game_:
        flash('No games existing')
        return redirect(url_for('games'))

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(list(columns.keys()) + activities)
    for team in game_.teams:
        for input_ in team.inputs.order_by(Input.active_at_day.asc()).all():
            cw.writerow([getattr(input_, k) for k in columns] +
                        ['started' if ta.started_on_day == input_.active_at_day else
                         'initiated' if ta.initiated_on_day == input_.active_at_day else
                         'finished' if ta.finished_on_day == input_.active_at_day else
                         ''
                         for ta in input_.activities])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=results.csv"
    output.headers["Content-type"] = "text/csv"
    return output


def set_team_activity(team_act, team_, game_):
    id_splited = team_act.id.split('_')
    activity = Activity.query.filter_by(id=id_splited[-1]).first()
    team_act.activity_id = activity.id
    team_act.team_id = id_splited[1]
    team_act.game = id_splited[0]
    team_act.cost = activity.cost
    team_act.started_on_day = MAX_DAY
    team_act.finished_on_day = MAX_DAY
    team_act.initiated_on_day = game_.current_day
    team_act.first_time_ever_initiated_on_day = game_.current_day
    team_act.input_id = f'{game_.id}_{team_.id}_{game_.current_day}'
    commit_to_db(team_act)


def _reset_team_activity(id_):
    activity = TeamActivity.query.filter_by(id=id_).first()
    activity.started_on_day = MAX_DAY
    activity.finished_on_day = MAX_DAY
    activity.input_id = None
    activity.initiated_on_day = None
    commit_to_db(activity)
    return activity


def validate_and_update_credit(credit, input_):
    # should allow 0
    validation_error = False
    if credit in [0, None]:
        return True

    if credit > 0:
        if not credit % 300 == 0:
            flash(f'Credit should be increment of 300')
            validation_error = True
        if credit > 10000:
            flash(f'Maximum size of credit is 9900')
            validation_error = True
        if validation_error:
            return False

    input_.credit_to_take = credit
    db.session.add(input_)
    db.session.commit()
    return True


def _get_finished_activities(team_, game_):
    result = []
    for ta in TeamActivity.query.filter_by(team_id=team_.id, game=game_.id).all():
        if game_.current_day >= ta.finished_on_day:
            result.append(ta)
    return result
