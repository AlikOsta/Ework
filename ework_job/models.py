from django.db import models



class PostJob(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    image = models.ImageField(upload_to='postjob/', verbose_name='Изображение')
    salary = models.IntegerField(verbose_name='Зарплата')
    experience = models.IntegerField(verbose_name='Опыт работы')
    work_schedule = models.CharField(max_length=200, verbose_name='График работы')
    user = models.ForeignKey("User", on_delete=models.CASCADE, verbose_name='Автор')
    user_phone = models.CharField(max_length=200, verbose_name='Телефон')
    category = models.ForeignKey("CategoryJob", on_delete=models.CASCADE, verbose_name='Категория')
    location = models.CharField(max_length=200, verbose_name='Место работы')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")    
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    status = models.CharField(max_length=200, verbose_name='Статус')
    is_premium = models.BooleanField(default=False, verbose_name='Премиум')


class CategoryJob(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='category/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)






