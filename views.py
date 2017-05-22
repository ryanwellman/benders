from forms import *
from models import *

import re
import json as simplejson
from datetime import datetime
from annoying.decorators import render_to, ajax_request, JsonResponse
from annoying.functions import get_object_or_None as gooN
from json import dumps, loads
from decimal import *

from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail, BadHeaderError
from django.template import loader, Context
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers


@render_to('home.html')
def Home(request):
    season = GetSeason()
    players = Players.objects.all()
    now = datetime.now()
    news_rows = News.objects.filter(season=season).order_by('-when')

    schedule = Schedule.objects.filter(season=season).exclude(complete='yes').order_by('when')
    next_game_date = None 
    next_game_id = None
    next_game_number = None
    if schedule:
    	next_game_date = schedule[0].when.strftime("%B %d")
   	next_game_id = schedule[0].game_id
    	next_game_number = schedule[0].game_number

    player_rsvp_list = RSVP.objects.filter(game_id=next_game_id)
    rsvp_counter = len(player_rsvp_list)

    registered = False
    if request.user:
	for p in player_rsvp_list:
	    if request.user == p.player:
		registered = True

    context = dict()
    if not request.POST:
        context['form'] = UserRSVPForm()
	context['players'] = players
	context['now'] = now
	context['news_rows'] = news_rows
	context['next_game_date'] = next_game_date
	context['next_game_id'] = next_game_id
	context['next_game_number'] = next_game_number
	context['player_list'] = player_rsvp_list
	context['rsvp_counter'] = rsvp_counter
	context['registered'] = registered
        return context

    submit = request.POST.copy()

    form = UserRSVPForm(submit)
    if not form.is_valid():
        context['form'] = UserRSVPForm()
	context['players'] = players
	context['now'] = now
	context['news_rows'] = news_rows
	context['next_game_date'] = next_game_date
	context['next_game_id'] = next_game_id
	context['player_list'] = player_rsvp_list
	context['rsvp_counter'] = rsvp_counter
	context['registered'] = registered
        context['errors'] = form.errors
        return context

    username = submit['username']
    password = submit['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
	    registered_already = False
	    for r in player_rsvp_list:
		if r.player == user:
		    registered_already = True
	    if registered_already:
		messages.warning(request, 'Whoops...you have already registered for the next game and you can only play one stack at a time.  Good luck!')
		return redirect('home')
	    else:
	    	new_rsvp = RSVP()
	    	new_rsvp.player_id = user.id
	    	new_rsvp.game_id = next_game_id
	     	new_rsvp.save()
	    	messages.success(request, 'You have successfully submitted your RSVP for the next game.')
		EmailRSVPConfirmation(new_rsvp.player_id, new_rsvp.game_id)
            	return redirect('home')
        else:
            messages.error(request, 'Invalid login information.  Please reenter or signup if you have not done so.')
            return redirect('home')
    else:
        messages.error(request, 'Invalid login information.  Please reenter or signup if you have not done so.')
        return redirect('home')
    
    return dict(submit=submit)


def QuickRSVP(request):
    cs = GetSeason()
    schedule = Schedule.objects.filter(season=cs).exclude(complete='yes').order_by('when')
    next_game = schedule[0].game_id
    user = request.user
   
    player_rsvp_list = RSVP.objects.filter(game_id=next_game)

    submit = request.POST.copy()
    form = QuickRSVPForm()

    if not form.is_valid():
	errors = form.errors

    registered_already = False
    for r in player_rsvp_list:
    	if r.player == user:
            registered_already = True
    if registered_already:
       messages.warning(request, 'Whoops...you have already registered for the next game and you can only play one stack at a time.  Good luck!')
       return redirect('home')
    else:
    	new_rsvp = RSVP()
        new_rsvp.player_id = user.id
        new_rsvp.game_id = next_game
        new_rsvp.save()
        messages.success(request, 'You have successfully submitted your RSVP for the next game.')

	EmailRSVPConfirmation(new_rsvp.player_id, new_rsvp.game_id)
        return redirect('home')
    
    return {}


def EmailRSVPConfirmation(player_id, game_id):
    registered = User.objects.get(id=player_id)
    next_game = Schedule.objects.get(game_id=game_id)

    t = loader.get_template('after_registration.txt')
    c = Context({
	    'first_name': registered.first_name,
	    'game_number': next_game.game_number,
	    'when': next_game.when,
	})
    send_mail('You have registered for the next game!', t.render(c), 'admin@bendersgarage.com', [registered.email], fail_silently=False)

    return 


def UnRSVP(request):
    user = request.user
    cs = GetSeason()
    schedule = Schedule.objects.filter(season=cs).exclude(complete='yes').order_by('when')
    next_game = schedule[0].game_id

    rsvp_list = RSVP.objects.filter(game_id=next_game)
    remove_rsvp = rsvp_list.get(player_id=user)

    remove_rsvp.delete()

    messages.success(request, 'You have successfully deleted your RSVP for the next game.')

    return redirect('home')

     
@render_to('rsvp_list.html')
def RSVPList(request):
    schedule = list(Schedule.objects.all().exclude(complete='yes').order_by('when'))
    next_game_id = schedule[0].game_id
    next_game_number = schedule[0].game_number

    rsvp_list = list(RSVP.objects.filter(game_id=next_game_id))
    
    player_list = []
    for r in rsvp_list:
	player_dict = {}
	player = User.objects.filter(id=r.player_id)
	player_name = player[0].first_name + ' ' + player[0].last_name
	player_list.append(player_name)

    return dict(player_list=player_list,
		game_number=next_game_number)


@render_to('leaderboard.html')
def Leaderboard(request):
    get_season = GetSeason()
    first_game = Schedule.objects.filter(season=get_season, game_number='1')
    first_game = first_game[0]
    season = Season.objects.get(season=get_season)
    completed_games = Schedule.objects.filter(season=get_season, complete='yes').order_by('when')

    complete_ids = []
    complete_nums = []
    for cg in completed_games:
        complete_ids.append(cg.game_id)
        complete_nums.append(cg.game_number)

    last_game = None
    if len(complete_nums) > 0:
        last_game = complete_nums.pop()

    results = Results.objects.filter(season=season.id, game_id__in=complete_ids)

    p_w_results = []
    for r in results:
        p_w_results.append(r.player_id)

    players = list(set(p_w_results))

    season_results = []
    for r in results:
        s_result = {}
        s_result['game_number'] = r.game.game_number
        s_result['player_id'] = r.player_id
        s_result['first_name'] = r.player.first_name
        s_result['last_name'] = r.player.last_name
        s_result['total_points'] = r.total_points
        s_result['bounty_points'] = r.bounty_points
        season_results.append(s_result)

    #mobile = request.flavour

    return dict(players=dumps(players),
                season_results=dumps(season_results),
                last_game=dumps(last_game),
                has_results=last_game,
                first_game=first_game)

def GetSeason():
    season = CurrentSeason.objects.all()
    current_season = season[0].current_season

    return current_season


@render_to('weekly_results.html')
def WeeklyResults(request):
    current_season = GetSeason()
    schedule = Schedule.objects.filter(season=current_season).order_by('when')

    completed = []
    completed_games = []
    game_in_progress = False
    active_game = None
    for s in schedule:
        if s.in_progress:
            game_in_progress = True
            active_game = s
        if s.complete == 'yes':
            completed.append(s)
            completed_games.append(s)

    last_game = 1
    if len(completed) > 0:
        last_game = completed.pop()

    results = Results.objects.filter(season=12, busted=True).extra(select={'myinteger': 'CAST(place AS INTEGER)'}).order_by('myinteger')

    still_in = None
    if game_in_progress:
        still_in = list(RSVP.objects.filter(game=active_game))
        this_game = Results.objects.filter(game=active_game)
        for g in this_game:
            for s in still_in:
                if g.player_id == s.player_id and g.place is not None:
                    still_in.remove(s)

    games_with_results = []
    for r in results:
        games_with_results.append(r.game_id)
    games_with_results = list(set(games_with_results))

    game_list = []
    for s in schedule:
        game = {}
        game['number'] = s.game_number
        game['complete'] = s.complete
        game_list.append(game)

    weekly_info = []
    if active_game:
    	signed_up = RSVP.objects.filter(game=active_game)
    for g in game_list:
        game = {}
        rebuys = 0
        players = 0
        game['game'] = g['number']
        for r in results:
            if r.game.game_number == g['number']:
                rebuys += int(r.rebuys)
                players += 1
        game['rebuys'] = rebuys
        game['players'] = None
        if g['complete'] == 'yes':
            game['players'] = players
        if active_game and g['number'] == active_game.game_number:
            game['players'] = len(signed_up)
        weekly_info.append(game)

    return dict(schedule=schedule,
                last_game=last_game,
                results=results,
                weekly_info=dumps(weekly_info),
                games_with_results=games_with_results,
                completed_games=completed_games,
                still_in=still_in,
                game_in_progress=game_in_progress)


@render_to('schedule.html')
def SchedulePage(request):
    current_season = GetSeason()

    season_schedule = Schedule.objects.filter(season=current_season).order_by('when')
    winners = Results.objects.filter(place='1')

    schedule = [] 
    for s in season_schedule:
	game = {}
	game['game_number'] = s.game_number
	game['when'] = s.when
	winner = None
	for w in winners:
	    if w.game_id == s.game_id:
		winner = w
        game['winner'] = winner
	schedule.append(game)

    return dict(schedule=schedule,
                winners=winners)


@render_to('rules.html')
def Rules(request):
    return dict()


@render_to('toc.html')
def TOC(request):
    return dict()


@render_to('awards.html')
def LeagueAwards(request):
    awards = Awards.objects.all().order_by('id')

    return dict(awards=awards)


@render_to('hall_of_fame.html')
def Hall_Of_Fame(request):
    seasons = Season.objects.all().order_by('-id')

    hof = []
    for s in seasons:
	one_season = {}
	season_awards = HallOfFame.objects.filter(season=s.season)
	if not season_awards:
	    continue
	one_season['season'] = s.season
	one_season['year'] = s.year
	one_season['awards'] = season_awards
	hof.append(one_season)

    return dict(hof=hof)


def LogIn(request):
    context = dict()

    if not request.POST:
        context['form'] = UserLogInForm()
        return context

    submit = request.POST.copy()

    form = UserLogInForm(submit)
    if not form.is_valid():
        context['form'] = UserLogInForm()
        context['errors'] = form.errors
        return redirect('home')

    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
	if user.is_active:
	    login(request, user)
	    messages.success(request, 'Successfully logged in.')
	    return redirect('home')
   	else:
	    messages.error(request, 'Invalid login information.  Please reenter or signup if you have not done so.')
	    return redirect('invalid_login')
    else:
	messages.error(request, 'Invalid login information.  Please reenter or signup if you have not done so.')
	return redirect('invalid_login')
    return dict()


@render_to('invalid_login.html')
def InvalidLogin(request):
    context = dict()

    if not request.POST:
        context['form'] = UserLogInForm()
        return context

    submit = request.POST.copy()

    form = UserLogInForm(submit)
    if not form.is_valid():
        context['form'] = UserLogInForm()
        context['errors'] = form.errors
        return redirect('home')

    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            messages.success(request, 'Successfully logged in.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid login information.  Please reenter or signup if you have not done so.')
            return redirect('invalid_login')
    else:
        messages.error(request, 'Invalid login information.  Please reenter or signup if you have not done so.')
        return redirect('invalid_login')

    return dict()


@render_to('log_out.html')
def LogOut(request):
    logout(request)
    messages.success(request, 'Successfully logged out.')
    return redirect('home')


@render_to('benders_admin.html')
def BendersAdmin(request):
    if not request.user.is_staff:
	raise PermissionDenied()

    return dict()


@render_to('results_entry.html')
def ResultsEntry(request, game_number):
    if not request.user.is_staff:
	raise PermissionDenied()

    bal_mod_list = list(BalloonModifier.objects.all())
    payouts = serializers.serialize('json', PayoutTable.objects.all())
    get_season = CurrentSeason.objects.all()
    current_season = get_season[0].current_season
    game = Schedule.objects.get(season=current_season, game_number=game_number)
    game.in_progress = True
    game.save()

    players = RSVP.objects.filter(game_id=game.game_id)
    num_players = len(players)

    still_in = []
    busted_out = []
    rebuy_count = 0
    for p in players:
        result = gooN(Results, player=p.player_id, game=game)
        if not result:
            result = Results()
            result.player_id = p.player_id
            result.game_id = game.game_id
            result.season = Season.objects.get(season=current_season)
            result.save()
        if not result.busted:
            s_in = {}
            s_in['id'] = p.player.id
            s_in['full_name'] = p.player.first_name + ' ' + p.player.last_name
            s_in['place'] = None
            s_in['rebuys'] = result.rebuys
            s_in['bounty_points'] = result.bounty_points
            still_in.append(s_in)
        if result.busted:
            b_out = {}
            b_out['id'] = p.player.id
            b_out['full_name'] = p.player.first_name + ' ' + p.player.last_name
            b_out['place'] = result.place
            b_out['rebuys'] = result.rebuys
            b_out['bounty_points'] = result.bounty_points
            busted_out.append(b_out)
    busted_out = sorted(busted_out, key=lambda k: int(k['place']))

    rebuy_count = 0
    results = Results.objects.filter(game_id=game.game_id)
    for r in results:
        rebuy_count += int(r.rebuys)
    completed = gooN(CompletedGame, game_id=game.game_id)
    if not completed:
        completed = CompletedGame()
        completed.game = game
        completed.entries = num_players
        completed.total_rebuys = 0
        completed.base_points = 0
        completed.add_ons = 0
        completed.save()
    game_info = {}
    game_info['rebuys'] = completed.total_rebuys
    game_info['add_ons'] = completed.add_ons
    add_on_count = completed.add_ons

    bal_mod = []
    for bal in bal_mod_list:
        bal_dict = {}
        bal_dict['place'] = bal.place
        bal_dict['modifier'] = bal.modifier
        bal_mod.append(bal_dict)

    return dict(num_players=num_players,
                still_in=dumps(still_in),
                busted_out=dumps(busted_out),
                current_season=current_season,
                game_id=game.game_id,
                game_number=game_number,
                bal_mod=dumps(bal_mod),
                game_info=dumps(game_info),
                payouts=payouts,
                rebuy_count=rebuy_count,
		add_on_count=add_on_count)


@render_to('select_game.html')
def SelectGame(request):
    if not request.user.is_staff:
	raise PermissionDenied()

    current_season = GetSeason()
    game_list = Schedule.objects.filter(season=current_season).exclude(complete='yes').order_by('when')

    if request.POST:
        game_number = request.POST.get("game_number")
        game_in_progress = None
        for g in game_list:
            if g.in_progress:
                game_in_progress = g
        if game_in_progress and game_in_progress.game_number != game_number:
            messages.error(request, 'There is currently a game already in progress.  You cannot enter results for a different game until that game has been completed.')
            return redirect('select_game')
        return redirect('results_entry', game_number=game_number)

    return dict(game_list=game_list)


@render_to('assign_awards.html')
def AssignAwards(request):
    if not request.user.is_staff:
	raise PermissionDenied()
    award_list = list(Awards.objects.all())
    season_list = list(Season.objects.all())
    player_list = list(User.objects.all().order_by('last_name'))

    if request.POST:
	season = request.POST.get("selected_season")
	award = request.POST.get("selected_award")
	player = request.POST.get("selected_player")
	
	clean_season = re.sub(r"\D", "", season)
	clean_award = re.sub(r"\D", "", award)
	clean_player = re.sub(r"\D", "", player)

        hof = HallOfFame()
        hof.season = season
	hof.award_id = clean_award
	hof.player_id = clean_player
	hof.save()

	messages.success(request, 'Award assigned.')
	return redirect('http://bendersgarage.com/assign_awards')

    return dict(award_list=award_list,
		season_list=season_list,
		player_list=player_list)


@render_to('add_news.html')
def AddNews(request):
    if not request.user.is_staff:
	raise PermissionDenied()
    get_season = CurrentSeason.objects.get()
    current_season = get_season.current_season
    context = dict()

    if not request.POST:
	context['form'] = NewsForm()
	context['current_season'] = current_season
	return context

    #submit = request.POST.copy()

    #form = NewsForm(submit)
    
    form = NewsForm(request.POST, request.FILES)
 
    if not form.is_valid():
	context['form'] = form
	context['errors'] = form.errors
	return context

    news = form.save(commit=False)
    news.save()

    if "add_to_messageboard" in request.POST:
	mess = MessageBoard()
	mess.topic = news.title
	mess.who = request.user
	mess.message = news.news
	mess.save()

    messages.success(request, 'News added.')
    return redirect('benders_admin')


@render_to('create_schedule.html')
def CreateSchedule(request):
    if not request.user.is_staff:
	raise PermissionDenied()
    context = dict()
  
    if not request.POST:
	context['form'] = CreateScheduleForm()
	return context
    
    submit = request.POST.copy()

    form = CreateScheduleForm(submit)
    if not form.is_valid():
	context['form'] = CreateScheduleForm()
	context['errors'] = form.errors
	return context

    schedule = form.save(commit=False)
    schedule.save()
    messages.success(request, 'Game created.')
    return redirect('benders_admin')


@render_to('sign_up.html')
def SignUp(request):
    context = dict()

    if not request.POST:
	context['form'] = CreateUserForm()
	return context

    submit = request.POST.copy()

    form = CreateUserForm(submit)
    if not form.is_valid():
	context['form'] = form
	context['errors'] = form.errors
	return context
    
    new_user = User.objects.create_user(form.cleaned_data['username'],
					form.cleaned_data['email'],
					form.cleaned_data['password1'])
    new_user.first_name = form.cleaned_data['first_name']
    new_user.last_name = form.cleaned_data['last_name']
    new_user.save()
    full_name = new_user.first_name + new_user.last_name

    referred = ReferredBy()
    referred.user = new_user
    referred.referred_by = form.cleaned_data['referred_by']
    referred.save()

    staff = User.objects.filter(is_staff='True')
    if new_user:
	subject = 'A new user has requested to join Benders Garage'
	message = 'Benders Garage has received a new request to join the site from {0} {1}.  Please visit the admin section at www.bendersgarage.com/ to review this request.\n\nPlayer Name: {2}\nEmail: {3}'.format(new_user.first_name, new_user.last_name, full_name, new_user.email)
  	from_email = 'admin@bendersgarage.com'

	for s in staff:
	    try:
		send_mail(subject, message, from_email, [s.email])
	    except:
		pass

    new_user.is_active = False
    new_user.save()

    return redirect('home')


@render_to('review_registration.html')
def ReviewRegistration(request):
    if not request.user.is_staff:
	raise PermissionDenied()

    unactives = User.objects.filter(is_active=False).exclude(date_joined__lte='2014-06-18')
    referrals = ReferredBy.objects.all()

    if request.POST:
	activate = request.POST.get("activate_user")
	hmmm = request.POST.copy()
	messages.warning(request, 'We should activate {0}').format(hmmm)
	messages.success(request, 'User has been successfully activated.')
	return redirect('review_registration')

    return dict(unactives=unactives,
		referrals=referrals)


def ApproveRegistration(request, player_id):
    activate = User.objects.get(id=player_id)
    activate.is_active = True
    activate.save()

    t = loader.get_template('benders_welcome.txt')
    c = Context({
	    'first_name': activate.first_name,
     	})
    send_mail('Welcome to Benders Garage', t.render(c), 'admin@bendersgarage.com', [activate.email], fail_silently=False)
    messages.success(request, 'User has been succesfully activated.')

    return redirect('review_registration')


def DenyRegistration(request, player_id):
    deny = User.objects.get(id=player_id)
    deny.delete()

    messages.success(request, 'User has been denied registration.')

    return redirect('review_registration')


def DeactivatePlayer(request, player_id):
    deactivate = User.objects.get(id=player_id)
    deactivate.date_joined = '2001-01-01'
    deactivate.save()

    messages.success(request, 'User is deactivated.')

    return redirect('review_registration')


@render_to('accounting.html')
def LeagueAccounting(request):
    total_collected = 0
    weekly_payouts = 0
    league_fund = 0
    accounting = Accounting.objects.all()
    for a in accounting:
        total_collected += a.total_pot
        weekly_payouts += a.nightly_payout
        league_fund += a.toc_payout

    weekly_accounting = []
    for a in accounting:
        week = {}
        week['game_id'] = a.game.game_id
        week['game_number'] = a.game.game_number
        week['entry_money'] = a.entry_money
        week['rebuy_money'] = a.rebuy_money
        week['addon_money'] = a.addon_money
        week['total_pot'] = a.total_pot
        week['nightly_payout'] = a.nightly_payout
        week['toc_payout'] = a.toc_payout
        week['first_place'] = a.first_place
        week['second_place'] = a.second_place
        week['third_place'] = a.third_place
        week['fourth_place'] = a.fourth_place
        weekly_accounting.append(week)

    weekly_accounting = simplejson.dumps(weekly_accounting, cls=DjangoJSONEncoder)
    season = GetSeason()
    current_season = Season.objects.get(season=season)
    results = Results.objects.filter(season=current_season.id)
    players = User.objects.all().order_by('first_name')

    player_breakdown = []
    for p in players:
        player = {}
        player['id'] = p.id
        player['full_name'] = p.first_name + ' ' + p.last_name
        player['results'] = []
        for r in results:
            result = {}
            if r.place and p.id == r.player.id:
                result['game_number'] = r.game.game_number
                result['place'] = r.place
                result['rebuys'] = r.rebuys
		for a in accounting:
            	    if r.game_id == a.game_id:
			if r.place == '1':
			    result['money_won'] = float(a.first_place)
			if r.place == '2':
			    result['money_won'] = float(a.second_place)
			if r.place == '3':
			    result['money_won'] = float(a.third_place)
			if r.place == '4':
			    result['money_won'] = float(a.fourth_place)
                	if r.place == '5' and a.fifth_place:
			    result['money_won'] = float(a.fifth_place)
                	if r.place == '6' and a.sixth_place:
			    result['money_won'] = float(a.sixth_place)
                	if r.place == '7' and a.seventh_place:
			    result['money_won'] = float(a.seventh_place)
            	player['results'].append(result)
	if player['results']:
            player_breakdown.append(player)

    return dict(total_collected=total_collected,
                weekly_payouts=weekly_payouts,
                league_fund=league_fund,
		results=results,
                weekly_accounting=weekly_accounting,
                player_breakdown=dumps(player_breakdown))


@render_to('user_profile.html')
def UserProfile(request, user_id):
    u_id = str(user_id)
    req_id = str(request.user.id)
    if req_id != u_id:
	raise PermissionDenied()
	
    context = dict()
    #user_profile = Players.objects.get(user=user_id)
    user_profile = gooN(Players, user_id=user_id)
    first_name = request.user.first_name
    last_name = request.user.last_name

    initial = {}
    if user_profile:
	initial['nickname'] = user_profile.nickname
	initial['playing_since'] = user_profile.playing_since
	initial['tour_seasons'] = user_profile.tour_seasons
	initial['favorite_hand'] = user_profile.favorite_hand
	initial['best_memory'] = user_profile.best_memory
	initial['outside_activity'] = user_profile.outside_activity
	initial['photo'] = user_profile.photo

    if not request.POST:
	context['form'] = UserProfileForm(initial=initial)
	context['user_id'] = user_id
	context['first_name'] = first_name
	context['last_name'] = last_name
	return context

    if not user_profile:
	#submit = request.POST.copy()
	form = UserProfileForm(request.POST, request.FILES)
	if not form.is_valid():
	    context['form'] = UserProfileForm()
	    context['errors'] = form.errors
	    context['user_id'] = user_id
	    return context
	profile = form.save(commit=False)
	profile.user_id = user_id
	profile.save()
	messages.success(request, 'Profile Updated.')
	return redirect('home')
    else:
	form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
	form.user_id = user_id
	form.save()
	messages.success(request, 'Profile Updated.')
	return redirect('home')

    return dict()


@render_to('member_roster.html')
def MemberRoster(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    members = User.objects.filter(is_active=True).exclude(username='avaholic').order_by('first_name')

    inactive_members = User.objects.filter(is_active=False).exclude(username='avaholic').order_by('first_name')

    if 'deactivate' in request.POST:
        deact = User.objects.get(id=request.POST.get('id'))
        deact.is_active = False
        deact.save()
        messages.success(request, 'User deactivated.')
        return redirect('member_roster')

    if 'activate' in request.POST:
        act = User.objects.get(id=request.POST.get('id'))
        act.is_active = True
        act.save()
        messages.success(request, 'User activated.')
        return redirect('member_roster')

    if 'make_admin' in request.POST:
        admin = User.objects.get(id=request.POST.get('id'))
        admin.is_staff = True
        admin.save()
        messages.success(request, 'User has been given admin access.')
        return redirect('member_roster')

    if 'remove_admin' in request.POST:
        admin = User.objects.get(id=request.POST.get('id'))
        admin.is_staff = False
        admin.save()
        messages.success(request, 'User no longer has admin access.')
        return redirect('member_roster')

    if 'new_email' in request.POST:
        new = User.objects.get(id=request.POST.get('id'))
        new.email = request.POST.get('email_address')
        new.save()
        messages.success(request, 'Email udpated.')
        return redirect('member_roster')

    if 'update_name' in request.POST:
        name = User.objects.get(id=request.POST.get('id'))
        name.first_name = request.POST.get('first_name')
        name.last_name = request.POST.get('last_name')
        name.save()
        messages.success(request, 'Player name updated.')
        return redirect('member_roster')

    return dict(members=members, inactive_members=inactive_members)


@render_to('user_settings.html')
def UpdateUserSettings(request, user_id):
    u_id = str(user_id)
    req_id = str(request.user.id)
    if req_id != u_id:
	raise PermissionDenied

    context = dict()
    if not request.POST:
	context['form'] = UpdateUserForm(initial={'email': user.email})
	return context

    submit = request.POST.copy()
    #if submit['old_password']:
	#if submit['old_password'] != user.password
    
    return dict()


@render_to('player_list.html')
def PlayerList(request):
    player_list = User.objects.filter(is_active='True').exclude(last_name__isnull='True').exclude(username='teambg').exclude(username='avaholic').order_by('last_name')

    return dict(player_list=player_list)


@render_to('player_profile.html')
def PlayerProfile(request, player_id):
    profile = gooN(Players, user_id=player_id) 
    player = User.objects.get(id=player_id)

    trophy_case = HallOfFame.objects.filter(player=player)

    buy_ins = 0
    cashes = 0
    final_tables = 0
    wins = 0
    other = 0
    cash_no_win = 0
    ft_no_cash = 0
    bounty_points = 0
    weekly_results = []

    season = GetSeason()
    current_season = Season.objects.get(season=season)
    results = Results.objects.filter(player=player, season=current_season.id).order_by('game')
    other_players_results = Results.objects.filter(season=current_season.id)
    league_accounting = Accounting.objects.all()
    season_started = False
    if results:
	season_started = True
    no_games_played = False
    if not season_started and other_players_results:
   	no_games_played = True
    for r in results:
	buy_ins += 1
    	if r.place and int(r.place) <= 9:
	    final_tables += 1
	for a in league_accounting:
	    if r.game_id == a.game_id:
		if r.place in ['1', '2', '3', '4']:
		    cashes += 1
		if r.place == '5' and a.fifth_place:
		    cashes += 1
		if r.place == '6' and a.sixth_place:
		    cashes += 1
		if r.place == '7' and a.seventh_place:
		    cashes += 1
	if r.place and int(r.place) == 1:
	    wins += 1
	if r.place and int(r.place) > 9:
	    other += 1
	if r.place and int(r.place) > 4 and int(r.place) <=9:
	    ft_no_cash += 1
	if r.place and int(r.place) > 1 and int(r.place) <=4:
	    cash_no_win += 1
	bounty_points += int(r.bounty_points)
	week = {}
	week['game'] = r.game.game_number
	week['points'] = r.total_points
	weekly_results.append(week)

    final_table_pct = 0
    cash_pct = 0
    win_pct = 0
    if buy_ins > 0:
    	final_table_pct = float(final_tables)/float(buy_ins) * 100
    	cash_pct = float(cashes) / float(buy_ins) * 100 
    	win_pct = float(wins) / float(buy_ins) * 100
    league_games_played = len(Schedule.objects.filter(season=13, complete='yes'))
    
    all_players = User.objects.all()
    all_results = Results.objects.filter(season=12)
    standings = []
    for p in all_players:
    	points = 0
	sea_bounty_points = 0
	result = {}
	for r in all_results:
	    if r.player == p and r.total_points:
		points += int(r.total_points)
		sea_bounty_points += int(r.bounty_points)
	result['player'] = p
	result['points'] = points
	result['bounties'] = sea_bounty_points
	standings.append(result)

    new_standings = sorted(standings, key=lambda k: -k['points'])
    sorted_bounty = sorted(standings, key=lambda k: -k['bounties'])

    place = None
    current_points = 0
    for n in new_standings:
	if n['player'] == player:
	    place = new_standings.index(n) + 1
	    current_points = n['points']

    ninth_place = new_standings[8]['points']
    eighteenth_place = new_standings[17]['points']
    twentyseventh_place = new_standings[26]['points']

    points_away = None
    if results:
    	if place and place > 9 and place <= 18:
	    points_away = ninth_place - current_points
 	if place and place > 18 and place <= 27:
   	   points_away = eighteenth_place - current_points
    	if place and place > 27:
	   points_away = twentyseventh_place - current_points

    place_suffix = None
    if place and place in [1, 21, 31, 41, 51, 61, 71, 81, 91]:
	place_suffix = 'st'
    elif place and place in [2, 22, 32, 42, 52, 62, 72, 82, 92]:
 	place_suffix = 'nd'
    elif place and place in [3, 23, 33, 43, 52, 63, 73, 83, 93]:
	place_suffix = 'rd'
    else: 
	place_suffix = 'th'

    bounty_place = None
    for b in sorted_bounty:
	if b['player'] == player:
	    bounty_place = sorted_bounty.index(b) + 1

    bounty_place_suffix = None
    if bounty_place in [1, 21, 31, 41, 51, 61, 71, 81, 91]:
	bounty_place_suffix = 'st'
    elif bounty_place in [2, 22, 32, 42, 52, 62, 72, 82, 92]:
        bounty_place_suffix = 'nd'
    elif bounty_place in [3, 23, 33, 43, 52, 63, 73, 83, 93]:
        bounty_place_suffix = 'rd'
    else:
        bounty_place_suffix = 'th'

    json_stats = {}
    json_stats['buy_ins'] = buy_ins
    json_stats['cashes'] = cashes
    json_stats['other'] = other
    json_stats['ft_no_cash'] = ft_no_cash
    json_stats['wins'] = wins
    json_stats['cash_no_win'] = cash_no_win

    return dict(profile=profile,
		player=player,
		trophy_case=trophy_case,
		season_started=season_started,
		no_games_played=no_games_played,
		buy_ins=buy_ins,
		cashes=cashes,
		final_tables=final_tables,
		wins=wins,
		bounty_points=bounty_points,
		weekly_results=dumps(weekly_results),
		place=place,
		place_suffix=place_suffix,
		current_points=current_points,
		points_away=points_away,
		json_stats=dumps(json_stats),
		final_table_pct=final_table_pct, 
		cash_pct=cash_pct,
		win_pct=win_pct,
		league_games_played=league_games_played,
		bounty_place=bounty_place,
		bounty_place_suffix=bounty_place_suffix)


def NotifyPlayerFromProfile(request, player_id):
    player = gooN(User, id=player_id)

    if player:
    	subject = 'Uh Oh!  We have missing information...'
    	message = 'Hey, %s,\n\nSomeone visited your player profile page at bendersgarage.com and wanted to let you know that your profile still has not been filled out.  When you get a few minutes, consider updating your profile.\n\nThanks,\n\nBenders Team' % (player.first_name)
    	from_email = 'admin@bendersgarage.com'

    	try:
	    send_mail(subject, message, from_email, [player.email])
	    messages.success(request, 'Thanks for the heads up!  {0} has been notified.'.format(player.first_name))
    	except:
	    messages.error(request, 'Whoops.  Something went wrong and your message was not sent.  Management will be notified.')
    
    return redirect('player_profile', player_id=player_id)


@render_to('new_message.html')
def NewMessage(request):
    if not request.user.is_active:
	raise PermissionDenied()
    user = request.user.id
    context = dict()

    if not request.POST:
	context['form'] = MessageForm()
	context['user'] = user
   	return context

    submit = request.POST.copy()
    form = MessageForm(submit)
    if not form.is_valid():
	context['form'] = form
	context['errors'] = form.errors
	return context

    if form.is_valid():
        post = form.save(commit=False)
    	post.save()
    	messages.success(request, 'New Message Added.')

    	return redirect('message_board')

    return dict(user=user)

 
@render_to('message_board.html')
def MessageBoardHome(request):
    if not request.user.is_active:
	raise PermissionDenied()
    message_board = MessageBoard.objects.filter(parent_id=None).order_by('-when')

    message_list = []
    for m in message_board:
	mes = {}
	mes['id'] = m.id
	mes['topic'] = m.topic
	mes['who'] = m.who
	mes['when'] = m.when
	replies = MessageBoard.objects.filter(parent_id=m.id)
	mes['replies'] = len(replies)
	message_list.append(mes)

    return dict(message_list=message_list)


@render_to('message_thread.html')
def MessageThread(request, message_id):
    if not request.user.is_active:
	raise PermissionDenied()
    user = request.user.id
    parent_message = MessageBoard.objects.get(id=message_id)
    parent_player = Players.objects.get(user_id=parent_message.who.id)
    message_replies = MessageBoard.objects.filter(parent=message_id).order_by('when')
    context = dict()
    topic = 're: {0}'.format(parent_message.topic)

    replies = []
    for reply in message_replies:
	r = {}
	r['first_name'] = reply.who.first_name
	r['last_name'] = reply.who.last_name
	r['when'] = reply.when
	r['message'] = reply.message
	r['topic'] = reply.topic
	player = gooN(Players, user=reply.who)
	r['player'] = player
	replies.append(r)

    if not request.POST:
	context['form'] = MessageForm(initial={'topic': topic})
	#context['form'] = MessageForm()
	context['who'] = user
	context['parent_message'] = parent_message
	context['parent_player'] = parent_player
	context['message_id'] = message_id
	context['replies'] = replies
	return context

    submit = request.POST.copy()
    form = MessageForm(submit)
    if not form.is_valid():
	context['form'] = form
	context['errors'] = form.errors
	return context

    if form.is_valid():
	form = form.save(commit=False)
	form.save()
	messages.success(request, 'Reply successfully added.')

	return redirect('message_thread', message_id=message_id)
    
    return dict(user=user,
		message_id=message_id,
		parent_message=parent_message,
		parent_player=parent_player,
		replies=replies)


@csrf_exempt
@ajax_request
def AjaxAccounting(request):
    if not request.is_ajax():
	pass

    return dict()
    #return JsonResponse(dict())


@csrf_exempt
@ajax_request
def AjaxResults(request):
    if not request.is_ajax():
	pass

    ajax_data = request.GET.get('jsonData')
    game_id = request.GET.get('game_id')
    bust_out = request.GET.get('bust_out')
    next_result = loads(ajax_data)

    current_season = CurrentSeason.objects.all()
    c_season = current_season[0].current_season

    game_object = Schedule.objects.get(game_id=game_id)
    season_object = Season.objects.get(season=c_season)
    season = season_object.id

    player = None
    if bust_out == "False":
        player = User.objects.get(id=next_result['player_id'])
    if bust_out == "True":
        player = User.objects.get(id=next_result['player']['player_id'])

    result = gooN(Results, player=player.id, game=game_object)
    if not result:
        result = Results()
    if bust_out == "False":
        result.player_id = next_result['player_id']
        result.bounty_points = next_result['bounty_points']
        result.rebuys = next_result['indiv_rebuys']
    if bust_out == "True":
        result.busted = True
        result.player_id = next_result['player']['player_id']
        result.game_id = game_id
        result.place = next_result['place']
        result.total_points = next_result['total_points']
        result.tournament_points = next_result['tourney_points']
        result.bounty_points = next_result['player']['bounty_points']
        result.season_id = season
        result.rebuys = next_result['player']['indiv_rebuys']
        result.rebuy_mod = next_result['rebuy_mod']
        result.balloon_mod = next_result['balloon_mod']
        result.raw_percent = next_result['raw_percent']
        result.raw_points = next_result['raw_points']
        result.percent = next_result['percent']
    result.save()

    #return dict()
    return JsonResponse(dict(ajax_data=ajax_data, game_id=game_id))


@csrf_exempt
@ajax_request
def AjaxUndoResult(request):
    if not request.is_ajax():
        pass

    player_id = request.GET.get('player_id')
    game_id = request.GET.get('game_id')

    player = User.objects.get(id=player_id)
    game = Schedule.objects.get(game_id=game_id)
    result = gooN(Results, player=player, game=game)
    result.place = None
    result.busted = False
    result.save()

    #return dict()
    return JsonResponse(dict(player=player_id))


@csrf_exempt
@ajax_request
def AjaxAddOn(request):
    if not request.is_ajax():
        pass

    game_id = request.GET.get('game_id')
    add_ons = request.GET.get('add_ons')

    completed = gooN(CompletedGame, game_id=game_id)
    if completed:
        completed.add_ons = add_ons
        completed.save()

    #return dict()
    return JsonResponse(dict(add_ons=add_ons))


@csrf_exempt
@ajax_request
def RemoveNoShow(request):
    if not request.is_ajax():
        pass

    player_id = request.GET.get('player_id')
    game_id = request.GET.get('game_id')

    player = User.objects.get(id=player_id)
    game = Schedule.objects.get(game_id=game_id)
    no_show = gooN(RSVP, player_id=player_id, game_id=game_id)
    if no_show:
        no_show.delete()

    result = gooN(Results, player=player, game=game)
    result.delete()
    #return dict()
    return JsonResponse(dict(player_id=player_id))


@csrf_exempt
@ajax_request
def FinalizeGame(request):
    if not request.is_ajax():
        pass
    game_id = request.GET.get('game_id')
    entries = request.GET.get('entries')
    rebuys = request.GET.get('rebuys')
    base_points = request.GET.get('base_points')
    add_ons = request.GET.get('add_ons')
    first_place = request.GET.get('first_place')
    second_place = request.GET.get('second_place')
    third_place = request.GET.get('third_place')
    fourth_place = request.GET.get('fourth_place')
    prize_pool = request.GET.get('prize_pool')
    league_contribution = request.GET.get('league_contribution')

    schedule = gooN(Schedule, game_id=game_id)
    if schedule:
        schedule.complete = 'yes'
        schedule.in_progress = False
        schedule.save()

    completed = gooN(CompletedGame, game_id=game_id)
    if completed:
        completed.total_rebuys = rebuys
        completed.base_points = base_points
        completed.add_ons = add_ons
        completed.save()

    account = Accounting()
    account.game_id = game_id
    account.entry_money = int(entries) * 40
    account.rebuy_money = int(rebuys) * 20
    account.addon_money = int(add_ons) * 10
    account.total_pot = account.entry_money + account.rebuy_money + account.addon_money
    account.nightly_payout = account.entry_money
    account.toc_payout = int(league_contribution)
    account.first_place = int(first_place)
    account.second_place = int(second_place)
    account.third_place = int(third_place)
    account.fourth_place = int(fourth_place)
    account.save()

    #return dict()
    return JsonResponse(dict(rebuys=rebuys))


@render_to('add_site_images.html')
def AddSiteImages(request):
    if not request.user.is_staff:
	raise PermissionDenied()
    errors = None

    if request.POST:
	form = ImageUploadForm(request.POST, request.FILES)

	if form.is_valid():
	    pic = SitePictures()
	    pic.model_pic = form.cleaned_data['image']
	    pic.save()
	    messages.success(request, 'Image uploaded successfully!')
 	if not form.is_valid():
	    errors = form.errors
	    messages.error(request, 'Your shit didnt work bitch')
	    
    return dict(errors=errors)


@render_to('tournament_clock.html')
def TournamentClock(request, game_id):
    players = len(RSVP.objects.filter(game=game_id))
    game_info = Schedule.objects.get(game_id=game_id)
    still_in = len(Results.objects.filter(game=game_id, place=None))
    results = Results.objects.filter(game=game_id)
    rebuys = 0
    for r in results:
        rebuys += int(r.rebuys)
    completed = CompletedGame.objects.get(game=game_id)
    add_ons = completed.add_ons

    players_still_in = results.filter(place=None)
    player_list = []
    for si in players_still_in:
        player = {}
        player['id'] = si.player.id
        player['name'] = si.player.first_name + ' ' + si.player.last_name
        player_list.append(player)

    seats = TournamentSeat.objects.filter(game=game_id)
    assigned_seats = []
    if seats:
        for s in seats:
            seat = {}
            seat['id'] = s.player.id
            seat['name'] = s.player.first_name + ' ' + s.player.last_name
            seat['seat'] = s.seat
            seat['table'] = s.table
            assigned_seats.append(seat)

    blinds = BlindSchedule.objects.all()
    blind_structure = []
    for b in blinds:
        blind = {}
        blind['level'] = b.level
        blind['small'] = b.small
        blind['big'] = b.big
        blind_structure.append(blind)

    payouts = serializers.serialize('json', PayoutTable.objects.all())
    previous_progress = gooN(TournamentProgress, game=game_id)
    resume_at = {}
    if previous_progress:
        resume_at['current_level'] = previous_progress.current_level.level
        resume_at['minutes'] = previous_progress.minutes
        resume_at['seconds'] = previous_progress.seconds

    game_results = Results.objects.filter(game=game_id)
    finishers = []
    if game_results:
        for g in game_results:
            if g.place:
                finish = {}
                finish['place'] = g.place
                player = User.objects.get(id=g.player_id)
                finish['player'] = player.first_name + ' ' + player.last_name
                finish['points'] = g.total_points
                finishers.append(finish)

    return dict(game_id=game_id,
                game_number = game_info.game_number,
                players=players,
                still_in=still_in,
                rebuys=rebuys,
                add_ons=add_ons,
                player_list=dumps(player_list),
                blind_structure=dumps(blind_structure),
                payouts=payouts,
                assigned_seats=dumps(assigned_seats),
                resume_at=dumps(resume_at),
                finishers=dumps(finishers))


@csrf_exempt
@ajax_request
def UpdateTournamentInfo(request):
    if not request.is_ajax():
        pass

    game_id = request.GET.get('game_id')

    players = len(RSVP.objects.filter(game=game_id))
    still_in = len(Results.objects.filter(game=game_id, place=None))
    results = Results.objects.filter(game=game_id)
    rebuys = 0
    for r in results:
        rebuys += int(r.rebuys)
    completed = CompletedGame.objects.get(game=game_id)
    add_ons = int(completed.add_ons)
    still_in_ids = []
    busted_out = []
    for r in results:
        if not r.place:
            still_in_ids.append(r.player.id)
        if r.place:
	    busted = {}
            initial = r.player.last_name[:1]
            busted['player'] = r.player.first_name + ' ' + initial + '.'
            busted['place'] = r.place
            busted['points'] = r.total_points
            busted_out.append(busted)

    #return dict()
    return JsonResponse(dict(players=players,
                             still_in=still_in,
                             rebuys=rebuys,
                             add_ons=add_ons,
                             still_in_ids=still_in_ids,
                             busted_out=busted_out))


@csrf_exempt
@ajax_request
def AssignSeats(request):
    if not request.is_ajax():
        pass

    game_id = request.GET.get('game_id')
    player_id = request.GET.get('player_id')
    table = request.GET.get('table')
    seat = request.GET.get('seat')
    action = request.GET.get('action')

    if player_id and action == 'assign':
        assigned = TournamentSeat()
        assigned.game = Schedule.objects.get(game_id=game_id)
        assigned.player = User.objects.get(id=player_id)
        assigned.table = int(table)
        assigned.seat = int(seat)
        assigned.save()

    if action == 'remove':
        assigned = gooN(TournamentSeat, game=game_id, player=player_id)
        if assigned:
            assigned.delete()

    if action == 'combine':
        assigned = gooN(TournamentSeat, game=game_id, player=player_id)
        if assigned:
            assigned.table = int(table)
            assigned.seat = int(seat)
            assigned.save()

    #return dict()
    return JsonResponse(dict(player_id=player_id, game_id=game_id, table=table, seat=seat))


@csrf_exempt
@ajax_request
def AjaxTournamentProgress(request):
    if not request.is_ajax():
        pass

    game_id = request.GET.get('game_id')
    current_level = request.GET.get('current_level')
    minutes = request.GET.get('minutes')
    seconds = request.GET.get('seconds')

    previous = gooN(TournamentProgress, game=game_id)
    if previous:
        previous.current_level = BlindSchedule.objects.get(level=current_level)
        previous.minutes = minutes
        previous.seconds = seconds
        previous.save()
    else:
        progress = TournamentProgress()
        progress.game = Schedule.objects.get(game_id=game_id)
        progress.current_level = BlindSchedule.objects.get(level=current_level)
        progress.minutes = minutes
        progress.seconds = seconds
        progress.save()

    #return dict()
    return JsonResponse(dict(game_id=game_id, current_level=current_level, minutes=minutes, seconds=seconds))


@render_to('select_schedule.html')
def SelectSchedule(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    season = GetSeason()
    schedule = Schedule.objects.filter(season=season).exclude(complete='yes').order_by('game_id')

    if request.POST:
        schedule_id = request.POST.get('schedule_id')
        return redirect('edit_schedule', schedule_id=schedule_id)

    return dict(schedule=schedule)


@render_to('edit_schedule.html')
def EditSchedule(request, schedule_id):
    if not request.user.is_staff:
        raise PermissionDenied()

    editable = Schedule.objects.get(game_id=schedule_id)
    initial = {}
    initial['when'] = editable.when
    initial['game_number'] = editable.game_number
    initial['season'] = editable.season

    context = {}
    if not request.POST:
        context['form'] = CreateScheduleForm(initial=initial)
        return context

    form = CreateScheduleForm(request.POST, request.FILES, instance=editable)
    if not form.is_valid():
        context['form'] = CreateScheduleForm(initial=initial)
        context['errors'] = form.errors
        return context
    form.save()

    messages.success(request, 'Schedule Updated.')

    return redirect('benders_admin')


@render_to('register_player.html')
def RegisterPlayer(request):
    if not request.user.is_staff:
	raise PermissionDenied()

    current_season = GetSeason()
    full_schedule = Schedule.objects.filter(season=current_season, complete='').exclude(complete='yes').order_by('when')
    full_players = User.objects.filter(is_active=True).exclude(id=1).exclude(id=79).order_by('first_name')

    schedule = []
    for f in full_schedule:
	sch = {}
	sch['game_id'] = f.game_id
	sch['when'] = f.when.strftime("%B %d")
	sch['game_number'] = f.game_number
	schedule.append(sch)

    players = []
    for f in full_players:
 	ply = {}
	ply['id'] = f.id
	ply['first_name'] = f.first_name
	ply['last_name'] = f.last_name
	players.append(ply)
    
    return dict(schedule=dumps(schedule), players=dumps(players))


@csrf_exempt
@ajax_request
def AdminRSVP(request):
    if not request.is_ajax():
        pass

    game_id = request.GET.get('game_id')
    player_id = request.GET.get('player_id')

    reserve = RSVP()
    reserve.player=User.objects.get(id=player_id)
    reserve.game=Schedule.objects.get(game_id=game_id)
    reserve.save()

    return JsonResponse(dict(game_id=game_id, player_id=player_id))

