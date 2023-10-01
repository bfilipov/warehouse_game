import logging
import os

from app import db, create_app, Config
from app.models import Activity, ActivityRequirement, Game, Team, User


app = create_app(Config)
logger = logging.Logger(__name__)


class ActivityAdder:
    activities = [
        {'id': 'A', 'title': 'Строителен ремонт на склада (Дейност А)', 'days_needed': 20, 'cost': 1800,
         'depends_on': ''},
        {'id': 'B', 'title': 'Строителен ремонт на офис помещението (Дейност B)', 'days_needed': 10, 'cost': 600,
         'depends_on': ''},
        {'id': 'C', 'title': 'Изготвяне на организационен и архитектурен проект (Дейност C)', 'days_needed': 20,
         'cost': 300,
         'depends_on': ''},
        {'id': 'D', 'title': 'Оформяне на фасадата на склада – декоративни елементи, фирмено табло (Дейност D)',
         'days_needed': 10, 'cost': 1200, 'depends_on': ''},
        {'id': 'E', 'title': 'Доставка на съоръжения, окомплектоващи материали (Дейност E)', 'days_needed': 40,
         'cost': 3000,
         'depends_on': ''},
        {'id': 'F', 'title': 'Проектиране обзавеждането на склада и офиса (Дейност F)', 'days_needed': 10, 'cost': 300,
         'depends_on': 'C'},
        {'id': 'G', 'title': 'Поръчка и доставка на обзавеждането за склада (Дейност G)', 'days_needed': 20,
         'cost': 3000,
         'depends_on': '	A,B,F'},
        {'id': 'H', 'title': 'Поръчка и доставка на обзавеждането на офиса (Дейност H)', 'days_needed': 20, 'cost': 600,
         'depends_on': 'A,B,F'},
        {'id': 'I', 'title': 'Монтаж на обзавеждането в склада (Дейност I)', 'days_needed': 10, 'cost': 300,
         'depends_on': 'A,B,F,G'},
        {'id': 'J', 'title': 'Монтажа на обзавеждането на офиса (Дейност J)', 'days_needed': 10, 'cost': 900,
         'depends_on': 'A,B,F,H'},
        {'id': 'K', 'title': 'Поръчка и доставка на стоки (Дейност K)', 'days_needed': 30, 'cost': 3000,
         'depends_on': 'I'},
        {'id': 'L',
         'title': 'Монтаж на съоръжения, подредба и организация на склада (до редовната работа) (Дейност L)',
         'days_needed': 10,
         'cost': 300, 'depends_on': 'A,B,C,D,E,F,G,H,I,J,K'}]

    dependencies = [{'F': 'C'},
                    {'G': 'A'},
                    {'G': 'B'},
                    {'G': 'F'},
                    {'H': 'A'},
                    {'H': 'B'},
                    {'H': 'F'},
                    {'I': 'A'},
                    {'I': 'B'},
                    {'I': 'F'},
                    {'I': 'G'},
                    {'J': 'A'},
                    {'J': 'B'},
                    {'J': 'F'},
                    {'J': 'H'},
                    {'K': 'I'},
                    {'L': 'A'},
                    {'L': 'B'},
                    {'L': 'C'},
                    {'L': 'D'},
                    {'L': 'E'},
                    {'L': 'F'},
                    {'L': 'G'},
                    {'L': 'H'},
                    {'L': 'I'},
                    {'L': 'J'},
                    {'L': 'K'}]

    def create_activities(self):
        for a in self.activities:
            activity = Activity(id=a["id"], title=a["title"], days_needed=a["days_needed"], cost=a["cost"])
            db.session.add(activity)
            db.session.commit()

    def create_dependencies(self):
        for d in self.dependencies:
            act = next(iter(d))
            dependency = ActivityRequirement(activity_id=act, requirement_id=d[act])
            db.session.add(dependency)
            db.session.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        adder = ActivityAdder()
        adder.create_activities()
        adder.create_dependencies()
        logger.info('Created activities')

        game_ = Game()
        db.session.add(game_)
        db.session.commit()
        logger.info(f'Created game {game_}')

        admin_user = User()
        admin_user.username = 'admin'
        admin_user.display_name = 'admin'
        admin_user.is_admin = True
        admin_user.set_password(os.getenv('ADMIN_PASSWORD'))
        db.session.add(admin_user)
        db.session.commit()

        for i in range(1, 31):
            new_team = Team()
            new_team.display_name = f'Team{i}'
            new_team.game_id = game_.id
            db.session.add(new_team)
            db.session.commit()
            logger.info(f'Created new team {new_team}')

            new_user = User()
            new_user.username = f'user{i}'
            new_user.display_name = f'user{i}'
            new_user.email = new_user.username + '@warehouse-game.com'
            new_user.set_password(new_user.username + '321')
            new_user.is_manager = True
            new_user.team_id = new_team.id
            db.session.add(new_user)
            db.session.commit()
            logger.info(f'Created new user \n'
                        f'{new_user} pass {new_user.username + "321"}')
