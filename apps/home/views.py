from re import T
from sqlite3 import Date
from urllib.parse import uses_relative
from urllib.robotparser import RobotFileParser
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django.views import generic

from .models import Todo, Home, TodoCate, TodoPriority
from login.models import User
# from .forms import TodoForm
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
    print(request.POST)
    content = request.POST['content']
    priority = request.POST['priority']
    cate = request.POST['cate']
    user = request.POST['user']

    # 내 할 일 페이지에서 기타 카테고리가 아닌 카테고리
    if request.POST['cate'] != 'no-cate' and int(user) is request.user.id:
        print("내꺼 기타말고")
        todo = Todo.objects.create(home=request.user.home, content=content, cate=TodoCate.objects.get(id = cate), user = User.objects.get(id = user), 
        priority = TodoPriority.objects.get(id = priority), date = date)
    # 내 할 일 페이지에서 기타 카테고리
    elif (cate == 'no-cate') and int(user) is request.user.id:
        print("내꺼 기타")
        todo = Todo.objects.create(home=request.user.home, content=content, user = User.objects.get(id = user), 
        priority = TodoPriority.objects.get(id = priority), date = date)
    # 전체 할 일 페이지에서 담당없음 카테고리
    else:
        print("전체")
        todo = Todo.objects.create(home=request.user.home, content=content,
        priority = TodoPriority.objects.get(id = priority), date = date)
    
    todo.save()
    return redirect('home:date_todo', date = date)
    # if form.is_valid():
    #     print("valid")
    #     todo = form.save(commit=False)
    #     todo.home = current_home
    #     todo.date = date
    #     todo.save()
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
    complete_total_todos = total_todos.filter(is_done=True)
    user_todos = total_todos.filter(user__username = current_user.username, date = date, is_done=False)
    complete_user_todos = total_todos.filter(user__username = current_user.username, date = date, is_done=True)
 
    current_home = Home.objects.filter(user = current_user)[0]
    roommates = User.objects.filter(home=request.user.home)
    cates = TodoCate.objects.filter(home = current_home)

    user_todo_dict = make_todo_with_cate_dict(user_todos, cates)
    total_todo_dict = make_todo_with_cate_dict(total_todos, cates)
    no_user_todos = total_todos.filter(user=None)
    no_cate_user_todos = user_todos.filter(cate=None)
    doing_todos = total_todos.exclude(user=None).exclude(is_done=True)
    todo_priority = TodoPriority.objects.all()
    print(no_cate_user_todos)
    # form = TodoForm(current_home)

    ctx = {
        'select_date' : date,
        'total_todo_dict' : total_todo_dict,
        'user_todo_dict' : user_todo_dict,
        'complete_user_todos' : complete_user_todos,
        'complete_total_todos' : complete_total_todos,
        'no_user_todos' : no_user_todos,
        'no_cate_user_todos' : no_cate_user_todos,
        'doing_todos' : doing_todos,
        'username' : current_user.username,
        # 'form' : form,
        'cates' : cates,
        'todo_priority' : todo_priority,
        'roomates' : roommates
    }

    return render(request, 'home/date_todo/date_todo.html', context=ctx)

def make_todo_with_cate_dict(todos, cates):
    todo_dict= {}
    for cate in cates:
        todo_dict[cate] = todos.filter(cate=cate)
    return todo_dict
