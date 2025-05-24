# class-shark-bot
# config.py
Содержимое конфигурационного файла для корректной работы бота  
``` python
token = "ваш_токен"  
model = "ваша_модель.h5"  
webhook_url = "https://ваш_вебхук.a.free.pinggy.link/webhook"  
main_admins = ["user_id_главного_админа_1", "user_id_главного_админа_2"]
```

# База данных MySQL
Используйте эти команды для создания базы данных  
``` sql
CREATE DATABASE IF NOT EXISTS baby_shark;
```  
``` sql
use baby_shark;
```  

# Создание тунеля для вебхуков
Для создания тунеля пропишите в cmd команду  
``` shell
ssh -p 443 -R0:127.0.0.1:8000 a.pinggy.io
```
Вы получите ссылку вида `https://ваш_вебхук.a.free.pinggy.link/webhook`. Telegram требует именно https!  
Ссылка действует час. Её нужно вставить в `config.py`
