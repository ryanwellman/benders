from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

from settings import *
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'benders.views.home', name='home'),
    # url(r'^benders/', include('benders.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'benders.views.Home', name='home'),
    url(r'^quick_rsvp', 'benders.views.QuickRSVP', name='quick_rsvp'),
    url(r'^un_rsvp', 'benders.views.UnRSVP', name='un_rsvp'),
    url(r'^leaderboard/', 'benders.views.Leaderboard', name='leaderboard'),
    url(r'^weekly_results/', 'benders.views.WeeklyResults', name='weekly_results'),
    url(r'^schedule/', 'benders.views.SchedulePage', name='schedule'),
    url(r'^rules/', 'benders.views.Rules', name='rules'),
    url(r'^toc/', 'benders.views.TOC', name='toc'),
    url(r'^awards/', 'benders.views.LeagueAwards', name='awards'),
    url(r'^hall_of_fame/', 'benders.views.Hall_Of_Fame', name='hall_of_fame'),
    #url(r'^log_in_modal/', 'benders.views.LogIn', name='log_in_modal'),
    url(r'^log_in/', 'benders.views.LogIn', name='log_in'),
    url(r'^invalid_login', 'benders.views.InvalidLogin', name='invalid_login'),
    url(r'^log_out/', 'benders.views.LogOut', name='log_out'),
    url(r'^benders_admin/', 'benders.views.BendersAdmin', name='benders_admin'),
    url(r'^select_game/', 'benders.views.SelectGame', name='select_game'),
    url(r'^results_entry/(?P<game_number>[-\w]+)', 'benders.views.ResultsEntry', name='results_entry'),
    url(r'^assign_awards/', 'benders.views.AssignAwards', name='assign_awards'),
    url(r'^create_schedule/', 'benders.views.CreateSchedule', name='create_schedule'),
    url(r'^sign_up/', 'benders.views.SignUp', name='sign_up'),
    url(r'^review_registration', 'benders.views.ReviewRegistration', name='review_registration'),
    url(r'^deny_registration/(?P<player_id>[-\w]+)', 'benders.views.DenyRegistration', name='deny_registration'),
    url(r'^approve_registration/(?P<player_id>[-\w]+)', 'benders.views.ApproveRegistration', name='approve_registration'),
    url(r'^deactivate_player/(?P<player_id>[-\w]+)', 'benders.views.DeactivatePlayer', name='deactivate_player'),
    url(r'^member_roster', 'benders.views.MemberRoster', name='member_roster'),
    url(r'^user_profile/(?P<user_id>[-\w]+)', 'benders.views.UserProfile', name='user_profile'),
    url(r'^user_settings/(?P<user_id>[-\w]+)', 'benders.views.UpdateUserSettings', name='user_settings'),
    url(r'^player_list/', 'benders.views.PlayerList', name='player_list'),
    url(r'^player_profile/(?P<player_id>[-\w]+)', 'benders.views.PlayerProfile', name='player_profile'),
    url(r'^notify_player/(?P<player_id>[-\w]+)', 'benders.views.NotifyPlayerFromProfile', name='notify_player'),
    url(r'^add_news/', 'benders.views.AddNews', name='add_news'),
    url(r'^accounting/', 'benders.views.LeagueAccounting', name='accounting'),
    url(r'^new_message', 'benders.views.NewMessage', name='new_message'),
    url(r'^message_board/', 'benders.views.MessageBoardHome', name='message_board'),
    url(r'^message_thread/(?P<message_id>[-\w]+)', 'benders.views.MessageThread', name='message_thread'),
    url(r'^user/password/reset/$', 'django.contrib.auth.views.password_reset', {'post_reset_redirect' : '/user/password/reset/done/'}, name='password_reset'),
    url(r'^user/password/reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    url(r'^user/password/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', {'post_reset_redirect' : '/user/password/done/'}),
    url(r'^user/password/done/$', 'django.contrib.auth.views.password_reset_complete'),

    url(r'^ajax_results/', 'benders.views.AjaxResults', name='ajax_results'),
    url(r'^ajax_undo_result/', 'benders.views.AjaxUndoResult', name='ajax_undo_result'),
    url(r'^ajax_finalize_game/', 'benders.views.FinalizeGame', name='finalize_game'),
    url(r'^ajax_remove_noshow/', 'benders.views.RemoveNoShow', name='remove_no_show'),
    url(r'^ajax_accounting/', 'benders.views.AjaxAccounting', name='ajax_accounting'),
    url(r'^ajax_add_on/', 'benders.views.AjaxAddOn', name='ajax_add_on'),
    url(r'^ajax_admin_rsvp/', 'benders.views.AdminRSVP', name='ajax_admin_rsvp'),

    url(r'^add_site_images/', 'benders.views.AddSiteImages', name='add_site_images'),

    url(r'^rsvp_list', 'benders.views.RSVPList', name='rsvp_list'),
  
    url(r'^tournament_clock/(?P<game_id>[-\w]+)', 'benders.views.TournamentClock', name='tournament_clock'),
    url(r'^update_tournament_info/', 'benders.views.UpdateTournamentInfo', name='update_tournament_info'),
    url(r'^ajax_assignseats/', 'benders.views.AssignSeats', name='ajax_assignseats'),
    url(r'^ajax_tournament_progress/', 'benders.views.AjaxTournamentProgress', name='ajax_tournament_progres'),
    url(r'^select_schedule/', 'benders.views.SelectSchedule', name='select_schedule'),
    url(r'^edit_schedule/(?P<schedule_id>[-\w]+)', 'benders.views.EditSchedule', name='edit_schedule'),
    url(r'^register_player/', 'benders.views.RegisterPlayer', name='register_player')
)

URL_MOUNT = r'^benders/'

urlpatterns += staticfiles_urlpatterns()
if settings.DEBUG:
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

