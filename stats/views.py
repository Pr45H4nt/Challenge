from django.shortcuts import render
from django.views.generic import ListView, CreateView, DeleteView, DetailView
from .models import Notice, CustomUser, timezone
from pages.models import TrackTodo
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from pages.mixins import MemberRequiredMixin, NotDemoUserMixin
from django.http import HttpResponseForbidden, Http404
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
import json
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.mixins import LoginRequiredMixin
from pages.models import Room, Session, Todo, TrackTodo
# Create your views here.

class NoticeView(LoginRequiredMixin,MemberRequiredMixin,ListView):
    template_name = 'notices.html'
    model = Notice
    context_object_name = 'notices'

    def get_queryset(self):
        queryset= super().get_queryset()
        self.room_id = self.kwargs.get("room_id")
        queryset= queryset.filter(room__id=self.room_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = Room.objects.filter(id=self.room_id).first()
        notices = context['notices']

        context.update({
            'room': room,
            'pinned_notices': notices.filter(is_pinned=True),
            'regular_notices': notices.filter(is_pinned=False),
            'pinned_count': notices.filter(is_pinned=True).count(),
            'total_notices': notices.count(),
            'today_notices': notices.filter(created_on__date=timezone.localdate()).count(),
            'authors': CustomUser.objects.filter(notices__room=room).distinct()
        })
        return context


class NoticeCreateView(LoginRequiredMixin,MemberRequiredMixin,CreateView):
    model = Notice
    fields = ['title', 'content', 'is_pinned', 'is_admin']
    template_name = 'notice_form.html'


    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.room = get_object_or_404(Room, id=self.kwargs.get('room_id'))
        if (form.instance.is_admin or form.instance.is_pinned) and self.request.user != form.instance.room.admin:
            raise PermissionDenied("No Permission")
        if form.instance.is_html:
            form.instance.is_html = False

        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        context['room'] = get_object_or_404(Room, id=self.kwargs.get('room_id'))
        return context


    def get_success_url(self):
        return reverse_lazy('room-notices', kwargs ={"room_id":self.kwargs.get('room_id')})



class DeleteNoticeView(LoginRequiredMixin,NotDemoUserMixin,DeleteView):
    model = Notice
    template_name = 'confirm.html'
    pk_url_kwarg = 'notice_id'

    def get_object(self, queryset = None):
        obj= super().get_object(queryset)
        if obj.author != self.request.user and obj.room.admin != self.request.user:
            raise PermissionDenied("No Permission")
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = f"Do you really want to delete \"{self.get_object().title}\" notice from \"{self.get_object().room} \"?"
        self.notice_url = reverse_lazy('room-notices', kwargs ={"room_id": self.get_object().room.id})
        context['referer'] = self.notice_url
        return context
    
    def get_success_url(self):
        return self.request.POST.get('referer')



def toggle_pin(request, notice_id):
    if request.method == "POST":
        notice_inst = get_object_or_404(Notice, id=notice_id)
        if request.user == notice_inst.room.admin:
            notice_inst.is_pinned = not notice_inst.is_pinned
            notice_inst.save()
    
        return redirect(reverse('room-notices', kwargs={'room_id': notice_inst.room.id}))




class SessionStats(LoginRequiredMixin,MemberRequiredMixin,DetailView):
    model = Session
    pk_url_kwarg = 'session_id'
    context_object_name = 'session'
    template_name = 'session/stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.get_object()
        
        # Basic session info
        context['session_stats'] = self.get_session_basic_stats(session)
        
        # Chart data
        daily_hours_data = self.get_daily_total_hours_data(session)
        daily_independent_day = self.get_daily_hours_data(session)
        top_tasks_data = self.get_top_tasks_data(session)
        performers_data = self.get_performers_data(session)
        timeline_data = self.get_timeline_data(session)
        individual_timeline_data = self.get_individual_timeline_data(session)
        
        # Serialize data for JavaScript
        context['daily_hours_json'] = json.dumps(daily_hours_data, cls=DjangoJSONEncoder)
        context['daily_independent_json'] = json.dumps(daily_independent_day, cls=DjangoJSONEncoder)
        context['top_tasks_json'] = json.dumps(top_tasks_data, cls=DjangoJSONEncoder)
        context['performers_json'] = json.dumps(performers_data, cls=DjangoJSONEncoder)
        context['timeline_json'] = json.dumps(timeline_data, cls=DjangoJSONEncoder)
        context['individual_timeline_json'] = json.dumps(individual_timeline_data, cls=DjangoJSONEncoder)
        
        # Keep original data for template access
        context['daily_hours_data'] = daily_hours_data
        context['daily_independent_data'] = daily_independent_day
        context['top_tasks_data'] = top_tasks_data
        context['performers_data'] = performers_data
        context['timeline_data'] = timeline_data
        context['individual_timeline_data'] = individual_timeline_data
        
        # Summary statistics
        context['summary_stats'] = self.get_summary_stats(session)
        return context
    
    def get_date_range(self, session):
        """Get complete date range for the session"""
        # Get the earliest and latest dates from TrackTodo entries
        tracktodos = TrackTodo.objects.filter(todo__session=session)
        
        if not tracktodos.exists():
            # If no data, use session start/end dates or current date
            started_at = session.started_at.date() if session.started_at else timezone.now().date()
            end_date = session.finished_at.date() if session.finished_at else timezone.now().date()
            # Handle if started_at/finished_at are already date objects
            if hasattr(session.started_at, 'date'):
                started_at = session.started_at.date() if session.started_at else timezone.now().date()
            else:
                started_at = session.started_at if session.started_at else timezone.now().date()
            
            if hasattr(session.finished_at, 'date'):
                end_date = session.finished_at.date() if session.finished_at else timezone.now().date()
            else:
                end_date = session.finished_at if session.finished_at else timezone.now().date()
            
            return started_at, end_date
        
        dates = tracktodos.values_list('day', flat=True)
        started_at = min(dates)
        end_date = max(dates)
        
        # Optionally, you can extend to session boundaries if available
        # Convert datetime to date if necessary
        session_start = session.started_at
        session_end = session.finished_at
        
        if session_start:
            if hasattr(session_start, 'date'):
                session_start = session_start.date()
            if session_start < started_at:
                started_at = session_start
                
        if session_end:
            if hasattr(session_end, 'date'):
                session_end = session_end.date()
            if session_end > end_date:
                end_date = session_end
            
        return started_at, end_date

    def generate_date_range(self, started_at, end_date):
        """Generate all dates between start and end date"""
        dates = []
        current_date = started_at
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        return dates

    def get_session_basic_stats(self, session):
        """get basic session information"""
        total_members = session.members.count()
        total_hours = sum(session.total_hours.values()) if session.total_hours else 0
        active_tasks = session.todos.filter(completed=False).count()
        total_tasks = session.todos.count()
        
        return {
            'name': session.name,
            'total_members': total_members,
            'total_hours': round(total_hours, 1),
            'active_tasks': active_tasks,
            'total_tasks': total_tasks,
            'status': 'Active' if session.is_active else 'Completed',
            'description': session.description or '',
            'started_at': session.started_at,
            'finished_at': session.finished_at
        }

    def get_daily_total_hours_data(self, session):
        """Get cumulative daily hours with all dates included"""
        tracktodos = TrackTodo.objects.filter(todo__session=session).order_by('day')
        
        # Get date range
        started_at, end_date = self.get_date_range(session)
        all_dates = self.generate_date_range(started_at, end_date)
        
        # Build hours data
        hours_data = defaultdict(float)
        for item in tracktodos:
            hours_data[item.day] += item.hours
        
        # Build complete data with all dates
        labels = []
        data = []
        cumulative = 0
        
        for day in all_dates:
            cumulative += hours_data.get(day, 0)  # Use 0 if no data for this day
            labels.append(day)
            data.append(cumulative)
        
        return {
            'labels': labels,
            'data': data
        }
    
    def get_daily_hours_data(self, session):
        """Get daily hours with all dates included"""
        tracktodos = TrackTodo.objects.filter(todo__session=session).order_by('day')
        
        # Get date range
        started_at, end_date = self.get_date_range(session)
        all_dates = self.generate_date_range(started_at, end_date)
        
        # Build hours data
        hours_data = defaultdict(float)
        for item in tracktodos:
            hours_data[item.day] += item.hours
        
        # Build complete data with all dates
        labels = []
        data = []
        
        for day in all_dates:
            labels.append(day)
            data.append(hours_data.get(day, 0))  # Use 0 if no data for this day
        
        return {
            'labels': labels,
            'data': data
        }

    def get_top_tasks_data(self, session):
        """Get top tasks by hours for bar chart"""
        # Get todos with their total hours
        todos_with_hours = []
        for todo in session.todos.all():
            total_hours = todo.total_hours
            if total_hours > 0:
                # Truncate task name if too long
                task_name = todo.task[:30] + "..." if len(todo.task) > 30 else todo.task
                todos_with_hours.append({
                    'task': task_name,
                    'hours': total_hours,
                    'user': todo.user.username
                })
        
        # Sort by hours and get top 10
        todos_with_hours.sort(key=lambda x: x['hours'], reverse=True)
        top_tasks = todos_with_hours[:10]
        
        # If no tasks, create sample data
        if not top_tasks:
            top_tasks = [
                {'task': 'No tasks yet', 'hours': 0, 'user': 'N/A'}
            ]
        
        return {
            'labels': [task['task'] for task in top_tasks],
            'data': [task['hours'] for task in top_tasks],
            'users': [task['user'] for task in top_tasks]
        }

    def get_performers_data(self, session):
        """Get top performers data for pie chart"""
        # Use the session's current_rankings property
        rankings = session.current_rankings
        
        if not rankings:
            return {
                'labels': ['No data available'],
                'data': [0],
                'colors': ['#E2E8F0']
            }
        
        # Get top 8 performers to avoid cluttering
        top_performers = rankings[:8]
        
        # Color palette for the chart
        colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
        ]
        
        # If there are more than 8 performers, group the rest as "Others"
        if len(rankings) > 8:
            others_hours = sum([performer[1] for performer in rankings[8:]])
            labels = [performer[0].username for performer in top_performers] + ['Others']
            data = [performer[1] for performer in top_performers] + [others_hours]
            chart_colors = colors[:8] + ['#95A5A6']
        else:
            labels = [performer[0].username for performer in top_performers]
            data = [performer[1] for performer in top_performers]
            chart_colors = colors[:len(top_performers)]
        
        return {
            'labels': labels,
            'data': data,
            'colors': chart_colors
        }

    def get_timeline_data(self, session):
        """Get timeline data with all dates included"""
        tracktodos = TrackTodo.objects.filter(todo__session=session).select_related('todo__user')
        
        # Get date range
        started_at, end_date = self.get_date_range(session)
        all_dates = self.generate_date_range(started_at, end_date)
        
        # Step 1: Gather daily hours per user
        user_day_hours = defaultdict(lambda: defaultdict(float))
        users = set()

        for item in tracktodos:
            user = item.todo.user
            day = item.day
            users.add(user)
            user_day_hours[user][day] += item.hours

        # Step 2: Build labels from all dates
        labels = [str(day) for day in all_dates]  # X-axis

        # Step 3: Build datasets per user (cumulative)
        datasets = []
        for user in users:
            data = []
            cumulative = 0
            for day in all_dates:
                cumulative += user_day_hours[user].get(day, 0)  # Use 0 if no data
                data.append(cumulative)

            datasets.append({
                'label': user.username,
                'data': data,
            })

        return {
            'labels': labels,
            'datasets': datasets
        }
    
    def get_individual_timeline_data(self, session):
        """Get individual timeline data with all dates included"""
        tracktodos = TrackTodo.objects.filter(todo__session=session).select_related('todo__user')
        
        # Get date range
        started_at, end_date = self.get_date_range(session)
        all_dates = self.generate_date_range(started_at, end_date)
        
        # Step 1: Gather daily hours per user
        user_day_hours = defaultdict(lambda: defaultdict(float))
        users = set()

        for item in tracktodos:
            user = item.todo.user
            day = item.day
            users.add(user)
            user_day_hours[user][day] += item.hours

        # Step 2: Build labels from all dates
        labels = [str(day) for day in all_dates]  # X-axis

        # Step 3: Build datasets per user (non-cumulative)
        datasets = []
        for user in users:
            data = []
            for day in all_dates:
                data.append(user_day_hours[user].get(day, 0))  # Use 0 if no data

            datasets.append({
                'label': user.username,
                'data': data,
            })

        return {
            'labels': labels,
            'datasets': datasets
        }

    def get_summary_stats(self, session):
        """Get additional summary statistics"""
        total_hours = sum(session.total_hours.values()) if session.total_hours else 0
        total_members = session.members.count()
        
        # Average daily hours per participant
        daily_data = self.get_daily_hours_data(session)
        total_days = len([d for d in daily_data['data'] if d > 0]) or 1
        avg_daily = (total_hours / total_members / total_days) if total_members > 0 else 0
        
        # Most productive day
        daily_hours = daily_data['data']
        if daily_hours and max(daily_hours) > 0:
            max_day_index = daily_hours.index(max(daily_hours))
            best_day_date = daily_data['labels'][max_day_index]
            best_day = best_day_date.strftime('%A')
        else:
            best_day = 'N/A'
        
        # Completion rate
        total_tasks = session.todos.count()
        completed_tasks = session.todos.filter(completed=True).count()
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Longest streak (consecutive days with activity)
        longest_streak = self.calculate_longest_streak(daily_data['data'])
        
        return {
            'avg_daily': round(avg_daily, 1),
            'best_day': best_day,
            'completion_rate': round(completion_rate),
            'longest_streak': longest_streak,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks
        }

    def calculate_longest_streak(self, daily_hours):
        """Calculate the longest consecutive streak of days with activity"""
        if not daily_hours:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for hours in daily_hours:
            if hours > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak


class UserSessionStats(LoginRequiredMixin, MemberRequiredMixin, DetailView):
    model = Session
    pk_url_kwarg = 'session_id'
    context_object_name = 'session'
    template_name = 'session/user_stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.get_object()
        
        # Get user from URL parameter or current user
        user_id = self.kwargs.get('user_id')
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                raise Http404("User not found")
        else:
            user = self.request.user
        
        # Verify user is a member of this session
        if not session.members.filter(id=user.id).exists():
            raise Http404("User is not a member of this session")
        
        context['target_user'] = user
        
        # Basic user session info
        context['user_session_stats'] = self.get_user_session_basic_stats(session, user)
        
        # Chart data for this user
        daily_hours_data = self.get_user_daily_hours_data(session, user)
        daily_cumulative_data = self.get_user_daily_cumulative_hours_data(session, user)
        user_tasks_data = self.get_user_tasks_data(session, user)
        comparison_data = self.get_user_comparison_data(session, user)
        
        # Serialize data for JavaScript
        context['daily_hours_json'] = json.dumps(daily_hours_data, cls=DjangoJSONEncoder)
        context['daily_cumulative_json'] = json.dumps(daily_cumulative_data, cls=DjangoJSONEncoder)
        context['user_tasks_json'] = json.dumps(user_tasks_data, cls=DjangoJSONEncoder)
        context['comparison_json'] = json.dumps(comparison_data, cls=DjangoJSONEncoder)
        
        # Keep original data for template access
        context['daily_hours_data'] = daily_hours_data
        context['daily_cumulative_data'] = daily_cumulative_data
        context['user_tasks_data'] = user_tasks_data
        context['comparison_data'] = comparison_data
        
        # User summary statistics
        context['user_summary_stats'] = self.get_user_summary_stats(session, user)
        
        return context

    def get_user_date_range(self, session, user):
        """Get complete date range for the user in this session"""
        # Get the earliest and latest dates from user's TrackTodo entries
        user_tracktodos = TrackTodo.objects.filter(todo__session=session, todo__user=user)
        
        if not user_tracktodos.exists():
            # If no data, use session start/end dates or current date
            if hasattr(session.started_at, 'date'):
                started_at = session.started_at.date() if session.started_at else timezone.now().date()
            else:
                started_at = session.started_at if session.started_at else timezone.now().date()
            
            if hasattr(session.finished_at, 'date'):
                end_date = session.finished_at.date() if session.finished_at else timezone.now().date()
            else:
                end_date = session.finished_at if session.finished_at else timezone.now().date()
            
            return started_at, end_date
        
        dates = user_tracktodos.values_list('day', flat=True)
        started_at = min(dates)
        end_date = max(dates)
        
        # Extend to session boundaries if available
        session_start = session.started_at
        session_end = session.finished_at
        
        if session_start:
            if hasattr(session_start, 'date'):
                session_start = session_start.date()
            if session_start < started_at:
                started_at = session_start
                
        if session_end:
            if hasattr(session_end, 'date'):
                session_end = session_end.date()
            if session_end > end_date:
                end_date = session_end
            
        return started_at, end_date

    def generate_date_range(self, started_at, end_date):
        """Generate all dates between start and end date"""
        dates = []
        current_date = started_at
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        return dates

    def get_user_session_basic_stats(self, session, user):
        """Get basic session information for a specific user"""
        user_todos = session.todos.filter(user=user)
        user_total_hours = sum([todo.total_hours for todo in user_todos])
        user_active_tasks = user_todos.filter(completed=False).count()
        user_completed_tasks = user_todos.filter(completed=True).count()
        user_total_tasks = user_todos.count()
        
        # Get user's rank in session
        rankings = session.current_rankings
        user_rank = None
        for i, (ranked_user, hours) in enumerate(rankings, 1):
            if ranked_user.id == user.id:
                user_rank = i
                break
        
        return {
            'session_name': session.name,
            'user_name': user.username,
            'user_total_hours': round(user_total_hours, 1),
            'user_active_tasks': user_active_tasks,
            'user_completed_tasks': user_completed_tasks,
            'user_total_tasks': user_total_tasks,
            'user_rank': user_rank,
            'total_members': session.members.count(),
            'session_status': 'Active' if session.is_active else 'Completed',
            'started_at': session.started_at,
            'finished_at': session.finished_at
        }

    def get_user_daily_hours_data(self, session, user):
        """Get daily hours data for a specific user with all dates included"""
        user_tracktodos = TrackTodo.objects.filter(
            todo__session=session, 
            todo__user=user
        ).order_by('day')

        # Get date range
        started_at, end_date = self.get_user_date_range(session, user)
        all_dates = self.generate_date_range(started_at, end_date)

        # Build hours data
        hours_data = defaultdict(float)
        for item in user_tracktodos:
            hours_data[item.day] += item.hours

        # Build complete data with all dates
        labels = []
        data = []

        for day in all_dates:
            labels.append(day)
            data.append(hours_data.get(day, 0))  # Use 0 if no data for this day

        return {
            'labels': labels,
            'data': data
        }

    def get_user_daily_cumulative_hours_data(self, session, user):
        """Get cumulative daily hours data for a specific user with all dates included"""
        user_tracktodos = TrackTodo.objects.filter(
            todo__session=session, 
            todo__user=user
        ).order_by('day')

        # Get date range
        started_at, end_date = self.get_user_date_range(session, user)
        all_dates = self.generate_date_range(started_at, end_date)

        # Build hours data
        hours_data = defaultdict(float)
        for item in user_tracktodos:
            hours_data[item.day] += item.hours

        # Build complete data with all dates
        labels = []
        data = []
        cumulative = 0

        for day in all_dates:
            cumulative += hours_data.get(day, 0)  # Use 0 if no data for this day
            labels.append(day)
            data.append(cumulative)

        return {
            'labels': labels,
            'data': data
        }

    def get_user_tasks_data(self, session, user):
        """Get user's tasks data for bar chart"""
        user_todos = session.todos.filter(user=user)
        
        tasks_with_hours = []
        for todo in user_todos:
            total_hours = todo.total_hours
            if total_hours > 0:
                # Truncate task name if too long
                task_name = todo.task[:30] + "..." if len(todo.task) > 30 else todo.task
                tasks_with_hours.append({
                    'task': task_name,
                    'hours': total_hours,
                    'completed': todo.completed
                })

        # Sort by hours and get all tasks (or limit to top 15)
        tasks_with_hours.sort(key=lambda x: x['hours'], reverse=True)
        user_tasks = tasks_with_hours[:15]  # Limit to top 15 tasks

        if not user_tasks:
            user_tasks = [
                {'task': 'No tasks yet', 'hours': 0, 'completed': False}
            ]

        return {
            'labels': [task['task'] for task in user_tasks],
            'data': [task['hours'] for task in user_tasks],
            'completed': [task['completed'] for task in user_tasks]
        }

    def get_user_comparison_data(self, session, user):
        """Get comparison data between user and session average/top performers"""
        # Get user's total hours
        user_total_hours = sum([todo.total_hours for todo in session.todos.filter(user=user)])
        
        # Get session statistics
        session_total_hours = sum(session.total_hours.values()) if session.total_hours else 0
        total_members = session.members.count()
        session_average = (session_total_hours / total_members) if total_members > 0 else 0
        
        # Get top performer hours
        rankings = session.current_rankings
        top_performer_hours = rankings[0][1] if rankings else 0
        
        return {
            'labels': ['You', 'Session Average', 'Top Performer'],
            'data': [
                round(user_total_hours, 1),
                round(session_average, 1),
                round(top_performer_hours, 1)
            ],
            'colors': ['#36A2EB', '#FFCE56', '#FF6384']
        }

    def get_user_summary_stats(self, session, user):
        """Get additional summary statistics for the user"""
        user_todos = session.todos.filter(user=user)
        user_total_hours = sum([todo.total_hours for todo in user_todos])
        
        # User's daily average
        daily_data = self.get_user_daily_hours_data(session, user)
        active_days = len([d for d in daily_data['data'] if d > 0]) or 1
        user_daily_avg = user_total_hours / active_days if active_days > 0 else 0
        
        # User's most productive day
        daily_hours = daily_data['data']
        if daily_hours and max(daily_hours) > 0:
            max_day_index = daily_hours.index(max(daily_hours))
            best_day_date = daily_data['labels'][max_day_index]
            best_day = best_day_date.strftime('%A')
            best_day_hours = max(daily_hours)
        else:
            best_day = 'N/A'
            best_day_hours = 0
        
        # User's completion rate
        total_user_tasks = user_todos.count()
        completed_user_tasks = user_todos.filter(completed=True).count()
        user_completion_rate = (completed_user_tasks / total_user_tasks * 100) if total_user_tasks > 0 else 0
        
        # User's longest streak
        user_longest_streak = self.calculate_longest_streak(daily_data['data'])
        
        # Comparison with session average
        session_total_hours = sum(session.total_hours.values()) if session.total_hours else 0
        total_members = session.members.count()
        session_average = (session_total_hours / total_members) if total_members > 0 else 0
        above_average = user_total_hours > session_average
        
        # Get user's rank
        rankings = session.current_rankings
        user_rank = None
        for i, (ranked_user, hours) in enumerate(rankings, 1):
            if ranked_user.id == user.id:
                user_rank = i
                break
        
        return {
            'user_daily_avg': round(user_daily_avg, 1),
            'best_day': best_day,
            'best_day_hours': round(best_day_hours, 1),
            'user_completion_rate': round(user_completion_rate),
            'user_longest_streak': user_longest_streak,
            'active_days': active_days,
            'above_average': above_average,
            'session_average': round(session_average, 1),
            'user_rank': user_rank,
            'total_members': total_members
        }

    def calculate_longest_streak(self, daily_hours):
        """Calculate the longest consecutive streak of days with activity"""
        if not daily_hours:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for hours in daily_hours:
            if hours > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak