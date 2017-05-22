from django.db import models
from django.contrib.auth.models import User


SEASONS = (
    ('1', 'One'),
    ('2', 'Two'),
    ('3', 'Three'),
    ('4', 'Four'),
    ('5', 'Five'),
    ('6', 'Six'),
    ('7', 'Seven'),
    ('8', 'Eight'),
    ('9', 'Nine'),
    ('10', 'Ten'),
    ('11', 'Eleven'),
    ('12', 'Twelve'),
    ('13', 'Thirteen'),
    ('14', 'Fourteen')
)


class Schedule(models.Model):
    game_id = models.AutoField(primary_key=True, max_length=4)
    when = models.DateTimeField()
    season = models.CharField(choices=SEASONS, max_length=3)
    complete = models.CharField(max_length=3, null=True, blank=True)
    game_number = models.CharField(max_length=2)
    in_progress = models.BooleanField(default=False)

    class Meta:
	db_table = 'schedule'


class Players(models.Model):
    user = models.OneToOneField(User)
    nickname = models.CharField(max_length=20, null=True, blank=True)
    playing_since = models.CharField(max_length=10, null=True, blank=True)
    tour_seasons = models.CharField(max_length=5, null=True, blank=True)
    favorite_hand = models.CharField(max_length=16, null=True, blank=True)
    best_memory = models.TextField(null=True, blank=True)
    outside_activity = models.CharField(max_length=20, null=True, blank=True)
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)    

    def __unicode__(self):
	return "{0}, {1}, {2}, {3}, {4}, {5}, {6}".format(self.user, self.nickname, self.playing_since, self.tour_seasons, self.favorite_hand, self.best_memory, self.outside_activity)

    class Meta:
	db_table = 'players'


class ReferredBy(models.Model):
    user = models.OneToOneField(User)
    referred_by = models.CharField(max_length=64)

    class Meta:
	db_table = 'referredby'


class News(models.Model):
    news = models.TextField()
    #game = models.ForeignKey(Schedule, related_name='news_game')
    when = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=20) 
    season = models.CharField(max_length=2)
    photo = models.ImageField(upload_to='news_photos/', null=True, blank=True)

    class Meta:
	db_table = 'news'


class RSVP(models.Model):
    player = models.ForeignKey(User, related_name='rsvp_players')
    game = models.ForeignKey(Schedule, related_name='rsvp_game')

    class Meta:
        db_table = 'rsvp'


class Awards(models.Model):
    award = models.CharField(max_length=30)
    description = models.TextField()

    class Meta:
	db_table = 'awards'


class HallOfFame(models.Model):
    season = models.CharField(max_length=2)
    award = models.ForeignKey(Awards, related_name='hof_awards')
    player = models.ForeignKey(User, related_name='hof_players')

    class Meta:
	db_table = 'hall_of_fame'


class Season(models.Model):
    season = models.CharField(max_length=3)
    year = models.CharField(max_length=4)

    class Meta:
	db_table = 'season'


class Results(models.Model):
    player = models.ForeignKey(User, related_name='results_player')
    game = models.ForeignKey(Schedule, related_name='results_schedule')
    busted = models.BooleanField(default=False)
    place = models.CharField(max_length=3, null=True, blank=True)
    tournament_points = models.CharField(max_length=4, null=True, blank=True)
    bounty_points = models.CharField(max_length=3, default='0')
    total_points = models.CharField(max_length=4, null=True, blank=True)
    season = models.ForeignKey(Season, related_name='results_season')
    rebuys = models.CharField(max_length=3, default='0')
    rebuy_mod = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    balloon_mod = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    raw_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    raw_points = models.CharField(max_length=4, null=True, blank=True)
    percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    add_on = models.BooleanField(default=True)
 
    class Meta:
	db_table = 'results'


class CurrentSeason(models.Model):
    current_season = models.CharField(primary_key=True, max_length=3)

    class Meta:
	db_table = 'current_season'


class BalloonModifier(models.Model):
    place = models.CharField(primary_key=True, max_length=2)
    modifier = models.CharField(max_length=5)

    class Meta:
	db_table = 'balloon_mod'


class CompletedGame(models.Model):
    game = models.ForeignKey(Schedule, related_name='completed_game_number')
    entries = models.CharField(max_length=3)
    total_rebuys = models.CharField(max_length=3)
    base_points = models.CharField(max_length=4)
    add_ons = models.CharField(max_length=3)
    
    class Meta:
	db_table = 'completed_game'


class Accounting(models.Model):
    game = models.ForeignKey(Schedule, related_name='accounting_game_number')
    entry_money = models.DecimalField(max_digits=8, decimal_places=2)
    rebuy_money = models.DecimalField(max_digits=8, decimal_places=2)
    addon_money = models.DecimalField(max_digits=8, decimal_places=2)
    total_pot = models.DecimalField(max_digits=8, decimal_places=2)
    nightly_payout = models.DecimalField(max_digits=8, decimal_places=2)
    toc_payout = models.DecimalField(max_digits=8, decimal_places=2)
    first_place = models.DecimalField(max_digits=8, decimal_places=2)
    second_place = models.DecimalField(max_digits=8, decimal_places=2)
    third_place = models.DecimalField(max_digits=8, decimal_places=2)
    fourth_place = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    fifth_place = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    sixth_place = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    seventh_place = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
	db_table = 'accounting'


class PayoutTable(models.Model):
    players = models.IntegerField(max_length=3)
    number_paid = models.IntegerField(max_length=2)
    first_place = models.DecimalField(max_digits=8, decimal_places=2)
    second_place = models.DecimalField(max_digits=8, decimal_places=2)
    third_place = models.DecimalField(max_digits=8, decimal_places=2)
    fourth_place = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    fifth_place = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    sixth_place = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    seventh_place = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'payout_table'


class MessageBoard(models.Model):
    topic = models.CharField(max_length=30)
    when = models.DateTimeField(auto_now_add=True)
    who = models.ForeignKey(User, related_name='message_user')
    message = models.TextField()
    parent = models.ForeignKey('self', blank=True, null=True)

    class Meta:
	db_table = 'message_board'


class SitePictures(models.Model):
    model_pic = models.ImageField(upload_to='site_uploads/', default='site_uploads/None/no-img.jpg')

    class Meta:
	db_table = 'site_pictures'


class TournamentSeat(models.Model):
    game = models.ForeignKey(Schedule, related_name='game_seat')
    player = models.ForeignKey(User, related_name='seat_player')
    table = models.IntegerField(max_length=1)
    seat = models.IntegerField(max_length=2)

    class Meta:
        db_table = 'tournament_seat'


class BlindSchedule(models.Model):
    level = models.IntegerField(max_length=2)
    small = models.IntegerField(max_length=6)
    big = models.IntegerField(max_length=6)

    class Meta:
        db_table = 'blind_schedule'


class TournamentProgress(models.Model):
    game = models.ForeignKey(Schedule, related_name='game_progress')
    current_level = models.ForeignKey(BlindSchedule, related_name='current_blind')
    minutes = models.IntegerField(max_length=2)
    seconds = models.IntegerField(max_length=2)

    class Meta:
        db_table = 'touranment_progess'

