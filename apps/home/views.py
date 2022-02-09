from sqlite3 import Date
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django.views import generic

from .models import Todo, Home, TodoCate
from .forms import TodoForm
from .utils import Calendar
from datetime import datetime, timedelta, date
import calendar


# Create your views here.
class CalendarView(generic.ListView):
    model = Todo
    template_name = 'home/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        d = get_date(self.request.GET.get('month', None))
        cal = Calendar(d.year, d.month)
        html_cal = cal.formatmonth(withyear=True)
        context['calendar'] = mark_safe(html_cal)
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)
        context['month'] = str(d.month)
        context['year'] = str(d.year)
        print(context)
        return context

def get_date(req_month):
    if req_month:
        year, month = (int(x) for x in req_month.split('-'))
        return date(year, month, day=1)
    return datetime.today()

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month


@login_required
def add_todo(request, date):
    current_user = request.user
    current_home = Home.objects.filter(user = current_user)[0]
    form = TodoForm(current_home, request.POST)
    print(form.errors)
    if form.is_valid():
        print("valid")
        todo = form.save(commit=False)
        todo.home = current_home
        todo.date = date
        todo.save()
        return

@login_required
def delete_todo(request, date, todo_id):
    todo_id = todo_id.split('-')[-1]
    print(todo_id.split('-')[-1])
    delete_todo = Todo.objects.get(id = todo_id)
    delete_todo.delete()
    return redirect('home:date_todo', date = date)


@login_required
def edit_todo(request, date, todo_id):
    todo_id = todo_id.split('-')[-1]
    edit_todo = Todo.objects.get(id = todo_id)
    edit_todo.content = request.POST['content']
    edit_todo.user.id = request.POST['user']
    edit_todo.cate.id = request.POST['cate']
    edit_todo.save()
    return redirect('home:date_todo', date = date)


@login_required
def date_todo(request, date):
    current_user = request.user
    total_todos = Todo.objects.filter(home__name = current_user.home.name, date = date)
    user_todos = total_todos.filter(user__username = current_user.username, date = date)
    current_home = Home.objects.filter(user = current_user)[0]
    cate = TodoCate.objects.filter(home__todo_cate__name = current_home.todo_cate.name)

    if request.method == "POST":
        add_todo(request, date)
        return redirect('home:date_todo', date = date)

    form = TodoForm(current_home)

    ctx = {
        'select_date' : date,
        'total_todos' : total_todos,
        'user_todos' : user_todos,
        'username' : current_user.username,
        'form' : form,
    }

    return render(request, 'home/date_todo/date_todo.html', context=ctx)