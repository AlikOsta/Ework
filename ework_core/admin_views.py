"""
Админские команды для мониторинга и управления задачами архивирования
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django_rq import get_scheduler, get_queue
from rq.job import Job
from django_rq import get_connection
from ework_core.tasks import archive_expired_posts, get_expiry_stats
import json


class TaskMonitorAdminView:
    """Админская панель для мониторинга задач"""
    
    def admin_view(self, request):
        """Основная страница мониторинга задач"""
        context = {
            'title': 'Мониторинг задач архивирования',
            'scheduler_status': self.get_scheduler_status(),
            'recent_jobs': self.get_recent_jobs(),
            'expiry_stats': get_expiry_stats(),
            'opts': {'app_label': 'ework_core'},
        }
        return render(request, 'admin/task_monitor.html', context)
    
    def get_scheduler_status(self):
        """Получить статус планировщика"""
        try:
            scheduler = get_scheduler('default')
            jobs = scheduler.get_jobs()
            
            archive_job = None
            for job in jobs:
                if 'archive_expired_posts' in job.func_name:
                    archive_job = {
                        'id': job.id,
                        'func_name': job.func_name,
                        'created_at': job.created_at,
                        'meta': getattr(job, 'meta', {})
                    }
                    break
            
            return {
                'active': True,
                'total_scheduled_jobs': len(jobs),
                'archive_job': archive_job
            }
        except Exception as e:
            return {
                'active': False,
                'error': str(e)
            }
    
    def get_recent_jobs(self):
        """Получить последние выполненные задачи"""
        try:
            connection = get_connection('default')
            # Получаем список завершенных задач из Redis
            finished_jobs = []
            
            # Это упрощенная версия - в реальности можно использовать
            # RQ Dashboard или собственную систему логирования
            return finished_jobs
        except Exception as e:
            return []
    
    def run_task_now(self, request):
        """Запустить задачу архивирования немедленно"""
        if request.method == 'POST':
            try:
                queue = get_queue('default')
                job = queue.enqueue(archive_expired_posts)
                
                messages.success(
                    request,
                    f'Задача архивирования запущена (ID: {job.id})'
                )
            except Exception as e:
                messages.error(
                    request,
                    f'Ошибка запуска задачи: {e}'
                )
        
        return HttpResponseRedirect(reverse('admin:task_monitor'))

# Экземпляр для использования в URLs
task_monitor = TaskMonitorAdminView()


# Добавляем URL patterns для админки
def get_task_admin_urls():
    return [
        path('task-monitor/', task_monitor.admin_view, name='task_monitor'),
        path('task-monitor/run-now/', task_monitor.run_task_now, name='run_task_now'),
    ]